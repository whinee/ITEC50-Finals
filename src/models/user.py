import bcrypt
from pydantic import BaseModel, EmailStr, Field
from typing import Annotated, Literal, List

class UserReg(BaseModel):
    email: EmailStr = Field(
        title="email",
        description="Allowed email address",
    )
    username: str = Field(
        title="username",
        min_length=1,
        max_length=32,
        description="Allowed length from 1 to 32.",
    )
    password: str = Field(
        title="password",
        min_length=6,
        max_length=32,
        description="Allowed length from 6 to 32.",
    )
    confirm_password: str = Field(
        title="password",
        min_length=6,
        max_length=32,
        description="Allowed length from 6 to 32.",
    )


class User(BaseModel):
    id: Annotated[int, Field(primary_key=True)]
    role: Annotated[
        List[Literal["patient", "professional"]],
        Field(sa_column=Column(sa.ARRAY(sa.TEXT), nullable=False)),
    ]
    username: str = Field(
        title="username",
        min_length=1,
        max_length=32,
        description="Allowed length from 1 to 32.",
    )
    password: str = Field(
        title="password",
        min_length=6,
        max_length=32,
        description="Allowed length from 6 to 32.",
    )


class Users(BaseUsers, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    role: Annotated[
        List[Literal["patient", "professional"]],
        Field(sa_column=Column(sa.ARRAY(sa.TEXT), nullable=False)),
    ]
    created_at: Annotated[
        datetime.datetime,
        Field(sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=False)),
    ]
    updated_at: Annotated[
        datetime.datetime,
        Field(sa_column=Column(sa.TIMESTAMP(timezone=True), nullable=True)),
    ]
    disabled: Annotated[bool, Field(sa_column=Column(sa.BOOLEAN, nullable=False))]

def hash_pw(pw: str):
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(12))


def comp_pw(pw: str, hash: str):
    return bcrypt.checkpw(pw.encode("utf-8"), hash.encode("utf-8"))
