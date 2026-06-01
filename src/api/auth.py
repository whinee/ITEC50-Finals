"""
Authentication Endpoints.

Exposes lightning-fast endpoints for user registration, login, session termination, and identity verification, secured by Argon2id.
"""

import base64
import datetime
import random
from datetime import UTC
from typing import Annotated

from captcha.image import ImageCaptcha
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from faker import Faker
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound
from sqlmodel import insert, select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.background import BackgroundTask
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_301_MOVED_PERMANENTLY,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from wonderwords import RandomWord

from src.api.preferences import normalize_theme, theme_cookie_params
from src.config.settings import settings
from src.db.main import get_session
from src.middlewares.auth import check_if_logged_in, get_session_cookie
from src.models.cookies import (
    decode_encrypted_cookie,
    set_default_cookie_params,
    set_default_cookie_params_with_encryption,
)
from src.schema import BaseUsers, Bookmark, JDNode, Tag, User
from src.security.constants import COOKIE_EXPIRES_AFTER
from src.security.jwt_service import Claims, JwtService, get_jwt_service
from src.security.kdf_pass import get_kdf
from src.utils.custom_response import CustomResponse
from src.utils.demo_cleanup import cleanup_demo_user
from src.utils.email import send_otp_email

router = APIRouter()

_rw = RandomWord()

ADJECTIVES = _rw.filter(
    include_parts_of_speech=["adjectives"],
    word_max_length=14,
    exclude_with_spaces=True,
)
NOUNS = _rw.filter(
    include_parts_of_speech=["nouns"],
    word_max_length=14,
    exclude_with_spaces=True,
)

random.shuffle(ADJECTIVES)
random.shuffle(NOUNS)

_adj_pool = list(ADJECTIVES)
_noun_pool = list(NOUNS)

email_adapter = TypeAdapter(EmailStr)


class LoginData(BaseModel):
    """
    Strictly typed payload for incoming authentication requests.

    Args:
        BaseModel (type): Pydantic inheritance.

    """

    identifier: str
    password: str
    captcha_answer: str


@router.get("/generate-username")
async def generate_username_route(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Generate a unique random username.

    Args:
        session (AsyncSession): Database session.

    Returns:
        dict: JSON response containing the generated username.

    """
    username = await generate_username(session)
    return {"username": username}


async def generate_username(session: AsyncSession) -> str:  # noqa: C901
    """
    Dynamically generates a globally unique, human-readable username.

    Leverages `wonderwords` to stitch together randomized adjective-noun combinations (e.g., 'fast_cheetah_42'). It aggressively polls the database in a loop to guarantee absolute collision avoidance before returning the minted username.

    Args:
        session (AsyncSession): The ultra-fast async database session.

    Returns:
        str: A mathematically unique human-readable username.

    """
    while True:
        if not _adj_pool:
            _adj_pool.extend(ADJECTIVES)
            random.shuffle(_adj_pool)
        if not _noun_pool:
            _noun_pool.extend(NOUNS)
            random.shuffle(_noun_pool)

        adj = _adj_pool.pop()
        noun = _noun_pool.pop()
        number = random.randint(1, 99)  # noqa: S311
        username = f"{adj}_{noun}_{number}"

        if len(username) > 32:
            continue

        result = await session.exec(select(User).where(User.username == username))
        if result.first() is None:
            return username


@router.post(path="/login", status_code=HTTP_200_OK)
async def login_user(  # noqa: C901
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    kdf: Annotated[Argon2id, Depends(get_kdf)],
    data: Annotated[LoginData, Form()],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
):
    """
    Authenticate users logging into DeciMark.

    This route performs a hyper-secure authentication sequence. It accepts either an E-mail or Username, dynamically routing the query based on Pydantic validation. It then defers to the Argon2id Key Derivation Function to rigorously verify the password hash against timing attacks. Upon success, it mints a symmetrically encrypted JWT and injects it securely into an HTTPOnly cookie.

    Args:
        request (Request): The raw HTTP request.
        response (Response): The FastAPI response endpoint.
        session (AsyncSession): Database session.
        jwt_service (JwtService): The cryptographic token engine.
        kdf (Argon2id): The state-of-the-art password hasher.
        data (LoginData): The strictly typed form data.
        is_logged_in (bool): Boolean context.

    Returns:
        JSONResponse: The brilliantly formatted custom response.

    """
    if is_logged_in:
        return CustomResponse.json_flash(
            message="You must logout first.",
            category="error",
            status_code=HTTP_406_NOT_ACCEPTABLE,
        )

    captcha_token = request.cookies.get("captcha_token")
    if not captcha_token:
        return CustomResponse.json_flash(
            message="Captcha missing. Please reload.",
            category="error",
            status_code=HTTP_400_BAD_REQUEST,
        )

    try:
        claims = jwt_service.verify(captcha_token)
        if not claims.sub or claims.sub.lower() != data.captcha_answer.strip().lower():
            return CustomResponse.json_flash(
                message="Invalid captcha answer.",
                category="error",
                status_code=HTTP_400_BAD_REQUEST,
            )
    except Exception:
        return CustomResponse.json_flash(
            message="Captcha expired or invalid. Please reload.",
            category="error",
            status_code=HTTP_400_BAD_REQUEST,
        )

    identifier = data.identifier.strip().lower()

    try:
        email_adapter.validate_python(identifier)
        is_email = True
    except ValidationError:
        is_email = False

    if is_email:
        statement = select(User).where(User.email == identifier)
    else:
        statement = select(User).where(User.username == identifier)

    result = await session.exec(statement)
    try:
        user = result.one()
        kdf.verify_phc_encoded(data.password.encode(), user.password)
    except InvalidKey:
        return CustomResponse.json_flash(
            message="Username, E-mail, or password is invalid",
            category="error",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    except NoResultFound:
        return CustomResponse.json_flash(
            message="Username, E-mail, or password is invalid",
            category="error",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    except BaseException:  # noqa: BLE001
        return CustomResponse.json_flash(
            message="Something went wrong",
            category="error",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )
    if settings.AUTH.OTP:
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))  # noqa: S311
        send_otp_email(user.email, otp)

        # Store OTP in a short-lived 2FA JWT
        issued_at = int(datetime.datetime.now(datetime.UTC).timestamp())
        expires_at = issued_at + 300  # 5 minutes
        claims = Claims(exp=expires_at, sub=f"{user.email}:{otp}", iat=issued_at)
        # Add custom claims for OTP (we'll just append it to the subject for simplicity)
        token = jwt_service.sign(claims)

        cookie_params = set_default_cookie_params_with_encryption(
            name="2fa_token",
            value=token,
            expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
        )

        return CustomResponse.json_flash(
            message="2FA Verification required. Check your email.",
            category="info",
            status_code=HTTP_200_OK,
            json={"redirect": "/login/2fa"},
            cookie_params=[
                cookie_params,
                theme_cookie_params(normalize_theme(user.theme)),
            ],
            headers={
                "HX-Redirect": "/login/2fa",
            },  # Assuming the frontend uses HTMX to redirect or handle it
        )

    # Issue real session if OTP is disabled
    issued_at = int(datetime.datetime.now(datetime.UTC).timestamp())
    expires_at = issued_at + COOKIE_EXPIRES_AFTER
    claims = Claims(exp=expires_at, sub=user.email, iat=issued_at)
    session_token = jwt_service.sign(claims=claims)

    cookie_params = set_default_cookie_params_with_encryption(
        name="session",
        value=session_token,
        expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
    )

    return CustomResponse.json_flash(
        message="Login successful!",
        category="success",
        status_code=HTTP_200_OK,
        cookie_params=[cookie_params, theme_cookie_params(normalize_theme(user.theme))],
        headers={"HX-Redirect": "/bookmarks"},
    )


@router.get(path="/decrypt_cookie")
async def decrypt_cookie(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    """
    Introspect the client's current session token.

    Primarily used for debugging or deep frontend state synchronization, this route safely unwraps the Fernet-encrypted cookie and returns the verified JWT claims without exposing any sensitive cryptographic secrets.

    Args:
        request (Request): The incoming request.
        jwt_service (JwtService): The cryptographic engine.
        is_logged_in (bool): Login state.
        session_cookie (str): The raw encrypted token.

    Returns:
        JSONResponse: The decoded token payload claims.

    """
    if not is_logged_in:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    return jwt_service.verify(decode_encrypted_cookie(session_cookie))


@router.get(path="/logout")
async def logout_user(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    """
    Securely terminates a user session and eradicates demo accounts.

    Intercepts the request, validates the existing JWT signature, and commands the browser to aggressively purge the HTTPOnly session cookie. If the departing user is a demo account, it forcefully executes cascading DELETE cascades across all relational tables to ensure absolute data hygiene, instantly vaporizing all generated bookmarks, tags, and nodes.

    Args:
        request (Request): Incoming request.
        response (Response): The HTTP response to modify.
        session (AsyncSession): Database session.
        jwt_service (JwtService): Token engine.
        is_logged_in (bool): Boolean state.
        session_cookie (str): The actual cookie payload to annihilate.

    Returns:
        RedirectResponse: The fast redirect back to `/login`.

    """
    if not is_logged_in:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    claims = jwt_service.verify(decode_encrypted_cookie(session_cookie))
    if claims is not None:
        email = claims.sub
        if email and email.endswith("@demo.decimark.com"):
            user = await session.scalar(select(User).where(User.email == email))
            if user:
                response.background = BackgroundTask(cleanup_demo_user, user.id)

        cookie_params = set_default_cookie_params(name="session")
        # NOTE: `delete_cookie` does not have the following params:
        # - value
        # - expires
        del cookie_params["value"]
        del cookie_params["expires"]
        response.delete_cookie(**cookie_params)
        response.headers["Location"] = "/login"
        response.status_code = HTTP_301_MOVED_PERMANENTLY
        return response
    return CustomResponse.http_code(
        request=request,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


@router.post(
    "/register",
    status_code=HTTP_201_CREATED,
)
async def register_new_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    kdf: Annotated[Argon2id, Depends(get_kdf)],
    payload: Annotated[BaseUsers, Form()],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
):
    """
    Register a brand new user into the DeciMark ecosystem.

    This route aggressively validates incoming form data against strictly typed Pydantic models. It executes high-speed `asyncpg` queries to ensure absolute uniqueness of the Email and Username before invoking the heavy Argon2id hashing mechanism on the password. If no username is provided, it autonomously falls back to the dynamic username generator.

    Args:
        request (Request): Incoming request.
        session (AsyncSession): High-speed database channel.
        kdf (Argon2id): Password derivation module.
        payload (BaseUsers): The strictly mapped new user schema.
        is_logged_in (bool): Login context state.

    Returns:
        JSONResponse: The successfully formatted onboarding response.

    """
    if is_logged_in:
        return CustomResponse.json_flash(
            message="You must logout first.",
            category="warning",
            status_code=HTTP_406_NOT_ACCEPTABLE,
        )

    email_statement = select(User).where(User.email == payload.email)
    email_results = await session.exec(email_statement)
    email_has_first = email_results.first()
    if email_has_first:
        return CustomResponse.json_flash(
            message="User with E-mail already exists.",
            category="warning",
            status_code=HTTP_409_CONFLICT,
        )

    if payload.username:
        username_statement = select(User).where(User.username == payload.username)
        username_results = await session.exec(username_statement)
        username_has_first = username_results.first()
        if username_has_first:
            return CustomResponse.json_flash(
                message="User with this username already exists.",
                category="warning",
                status_code=HTTP_409_CONFLICT,
            )
    else:
        payload.username = await generate_username(session=session)

    created_at = datetime.datetime.now(tz=UTC)
    updated_at = created_at
    theme = normalize_theme(request.cookies.get("theme"))
    user = User(
        created_at=created_at,
        updated_at=updated_at,
        role="normal",
        theme=theme,
        **payload.model_dump(),
    )
    key = kdf.derive_phc_encoded(payload.password.encode())
    user.password = key
    user.disabled = False
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return CustomResponse.json_flash(
        message="Logged in successfully!",
        category="success",
        status_code=HTTP_301_MOVED_PERMANENTLY,
        headers={
            "Location": "/",
        },
        cookie_params=theme_cookie_params(theme),
    )


async def seed_demo_account(session: AsyncSession, user_id: int):  # noqa: C901
    """Bulk inserts fake data for a demo account bypassing ORM overhead."""
    fake = Faker()
    bookmark_tag_junction = Tag.bookmarks.property.secondary  # type: ignore
    bookmark_jd_junction = JDNode.bookmarks.property.secondary  # type: ignore

    now = datetime.datetime.now(UTC)
    epoch = datetime.datetime(1970, 1, 1, tzinfo=UTC)

    def random_date():
        delta = now - epoch
        random_second = random.randrange(
            (delta.days * 24 * 60 * 60) + delta.seconds,
        )
        return epoch + datetime.timedelta(seconds=random_second)

    def generate_jd_code():
        part1 = f"{random.randint(10, 99):02d}"  # noqa: S311
        part2 = f"{random.randint(10, 99):02d}"  # noqa: S311
        code = f"{part1}.{part2}"
        if random.random() > 0.5:  # noqa: S311
            words = [
                "tech",
                "news",
                "code",
                "design",
                "work",
                "lyra",
                "school",
                "project",
                "dev",
            ]
            code += f"+{random.choice(words)}"  # noqa: S311
        return code

    res = await session.execute(text("SELECT coalesce(max(id), 0) + 1 FROM tags"))
    next_tag_id = res.scalar() or 1
    res = await session.execute(text("SELECT coalesce(max(id), 0) + 1 FROM jd_nodes"))
    next_jd_id = res.scalar() or 1
    res = await session.execute(text("SELECT coalesce(max(id), 0) + 1 FROM bookmarks"))
    next_bookmark_id = res.scalar() or 1

    tag_count = 100
    tag_ids = []
    tag_batch = []
    tag_titles = list({fake.word() for _ in range(200)})[:tag_count]

    for i in range(len(tag_titles)):
        t_id = next_tag_id
        next_tag_id += 1
        tag_ids.append(t_id)
        t_created = random_date()
        tag_batch.append(
            {
                "id": t_id,
                "user_id": user_id,
                "title": tag_titles[i],
                "color": fake.hex_color(),
                "note": (fake.sentence() if random.random() > 0.5 else None),
                "created_at": t_created,
                "updated_at": t_created,
            },
        )
    if tag_batch:
        await session.execute(insert(Tag).values(tag_batch))

    jd_count = 100
    jd_ids = []
    jd_batch = []
    for _ in range(jd_count):
        j_id = next_jd_id
        next_jd_id += 1
        jd_ids.append(j_id)
        jd_batch.append(
            {
                "id": j_id,
                "user_id": user_id,
                "code": generate_jd_code(),
            },
        )
    if jd_batch:
        await session.execute(insert(JDNode).values(jd_batch))

    bookmark_count = 10000
    b_batch = []
    b_tag_batch = []
    b_jd_batch = []

    titles = [fake.catch_phrase() for _ in range(100)]
    urls = [fake.url() for _ in range(100)]

    for b_idx in range(bookmark_count):
        b_id = next_bookmark_id
        next_bookmark_id += 1
        b_created = random_date()

        b_batch.append(
            {
                "id": b_id,
                "user_id": user_id,
                "title": random.choice(titles) + f" {b_idx}",  # noqa: S311
                "url": random.choice(urls),  # noqa: S311
                "note": (fake.sentence() if random.random() > 0.8 else None),
                "created_at": b_created,
                "updated_at": b_created,
            },
        )

        if tag_ids:
            num_tags = random.randint(1, 3)  # noqa: S311
            sampled_tags = random.sample(tag_ids, num_tags)
            for t_id in sampled_tags:
                b_tag_batch.append({"bookmark_id": b_id, "tag_id": t_id})

        if jd_ids:
            num_jds = random.randint(1, 3)  # noqa: S311
            sampled_jds = random.sample(jd_ids, num_jds)
            for j_id in sampled_jds:
                b_jd_batch.append({"bookmark_id": b_id, "jd_node_id": j_id})

        if len(b_batch) >= 5000:
            await session.execute(insert(Bookmark).values(b_batch))
            if b_tag_batch:
                await session.execute(insert(bookmark_tag_junction).values(b_tag_batch))
            if b_jd_batch:
                await session.execute(insert(bookmark_jd_junction).values(b_jd_batch))
            b_batch = []
            b_tag_batch = []
            b_jd_batch = []
            await session.commit()

    if b_batch:
        await session.execute(insert(Bookmark).values(b_batch))
        if b_tag_batch:
            await session.execute(insert(bookmark_tag_junction).values(b_tag_batch))
        if b_jd_batch:
            await session.execute(insert(bookmark_jd_junction).values(b_jd_batch))

    await session.commit()

    # Reset sequences
    await session.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('tags', 'id'), coalesce(max(id), 1)) FROM tags;",
        ),
    )
    await session.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('jd_nodes', 'id'), coalesce(max(id), 1)) FROM jd_nodes;",
        ),
    )
    await session.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('bookmarks', 'id'), coalesce(max(id), 1)) FROM bookmarks;",
        ),
    )
    await session.commit()


@router.post("/demo")
async def demo_login(
    session: Annotated[AsyncSession, Depends(get_session)],
    kdf: Annotated[Argon2id, Depends(get_kdf)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
):
    """
    Auto-provision and authenticate a demo account.

    Instantly generates a randomized username, creates a new user with a static dummy password, and logs them in.

    Args:
        session (AsyncSession): Database session.
        kdf (Argon2id): Key derivation function.
        jwt_service (JwtService): JWT service.

    Returns:
        dict: Success message with secure HTTP-only cookies injected.

    """
    demo_username = await generate_username(session)
    demo_email = f"{demo_username}@demo.decimark.com"
    demo_password = "demopassword123"  # noqa: S105

    password_hash = kdf.derive_phc_encoded(demo_password.encode())

    new_user = User(
        username=demo_username,
        email=demo_email,
        password=password_hash,
        role="normal",
        disabled=False,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    await seed_demo_account(session, new_user.id)

    issued_at = int(datetime.datetime.now(tz=datetime.UTC).timestamp())
    expires_at = issued_at + 86400  # 1 day

    claims = Claims(exp=expires_at, iat=issued_at, sub=new_user.email)
    jwt = jwt_service.sign(claims)

    cookie_params = set_default_cookie_params_with_encryption(
        name="session",
        value=jwt,
        expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
    )

    return CustomResponse.json(
        status_code=200,
        message="Logged in as demo user.",
        cookie_params=cookie_params,
    )


@router.get("/captcha")
async def generate_captcha(
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
):
    """
    Generate a self-hosted visual CAPTCHA.

    Generates a secure image captcha, returning the base64-encoded image and setting an encrypted HTTP-only cookie with the expected answer.

    Args:
        jwt_service (JwtService): Core JWT service.

    Returns:
        dict: Base64 captcha payload and sets `captcha_token` cookie.

    """
    import random
    import string

    chars = string.ascii_uppercase + string.digits
    captcha_text = "".join(random.choices(chars, k=5))  # noqa: S311

    image = ImageCaptcha(width=280, height=90)
    data = image.generate(captcha_text)

    b64_image = base64.b64encode(data.getvalue()).decode()

    # Store text in a short-lived JWT token to prevent tampering
    exp = int(
        (datetime.datetime.now(tz=UTC) + datetime.timedelta(minutes=5)).timestamp(),
    )
    claims = Claims(sub=captcha_text, exp=exp)
    captcha_jwt = jwt_service.sign(claims)

    return CustomResponse.json(
        status_code=HTTP_200_OK,
        json={"image": f"data:image/png;base64,{b64_image}"},
        cookie_params={"key": "captcha_token", "value": captcha_jwt, "httponly": True},
    )


@router.post(path="/verify-2fa", status_code=HTTP_200_OK)
async def verify_2fa(  # noqa: C901
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    otp: Annotated[str, Form()],
):
    """
    Validate the One-Time Password to finalize authentication.

    Args:
        request (Request): The incoming request.
        response (Response): The FastAPI response endpoint.
        session (AsyncSession): Database session.
        jwt_service (JwtService): The cryptographic token engine.
        otp (str): The provided OTP payload.

    Returns:
        JSONResponse: The brilliantly formatted custom response.

    """
    token_str = request.cookies.get("2fa_token")
    if not token_str:
        return CustomResponse.json_flash(
            message="2FA session expired.",
            category="error",
            status_code=HTTP_401_UNAUTHORIZED,
        )

    try:
        raw_token = decode_encrypted_cookie(token_str)
        payload = jwt_service.verify(raw_token)
    except Exception:  # noqa: BLE001
        return CustomResponse.json_flash(
            message="Invalid 2FA session.",
            category="error",
            status_code=HTTP_401_UNAUTHORIZED,
        )

    sub = payload.sub or ""
    actual_otp = sub.split(":")[1] if ":" in sub else None

    if actual_otp != otp.strip():
        if not (settings.TEST.SMTP and otp.strip() == "000000"):
            return CustomResponse.json_flash(
                message="Invalid OTP code.",
                category="error",
                status_code=HTTP_401_UNAUTHORIZED,
            )

    # In test mode, we might not have the correct subject format, so extract properly
    if settings.TEST.SMTP and otp.strip() == "000000":
        # Usually subject is "email:otp", but if we bypass, let's just get the email part
        sub_claim = payload.sub or ""
        email = sub_claim.split(":")[0] if ":" in sub_claim else sub_claim
    else:
        email = (payload.sub or "").split(":")[0]

    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.one()

    # Issue real session
    issued_at = int(datetime.datetime.now(datetime.UTC).timestamp())
    expires_at = issued_at + COOKIE_EXPIRES_AFTER
    claims = Claims(exp=expires_at, sub=user.email, iat=issued_at)
    session_token = jwt_service.sign(claims=claims)

    cookie_params = set_default_cookie_params_with_encryption(
        name="session",
        value=session_token,
        expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
    )

    # Delete 2fa token
    del_cookie = set_default_cookie_params(name="2fa_token")
    del del_cookie["value"]
    del del_cookie["expires"]
    response.delete_cookie(**del_cookie)

    return CustomResponse.json_flash(
        message="Login successful!",
        category="success",
        status_code=HTTP_200_OK,
        cookie_params=[cookie_params],
        headers={"HX-Redirect": "/bookmarks"},
    )
