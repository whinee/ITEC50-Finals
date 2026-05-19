# DeciMark

## License

See [LICENSE.md](./LICENSE.md) for more details. Please read carefully as the project is dual-licensed. If in doubt, do not hesitate to contact me and inquire about licensing.

## Initial setup

Requires [direnv](https://direnv.net/).

```bash
mkdir -p ~/.config/direnv
# Either copy or append the layout script
cat .direnv.uv >> ~/.config/direnv/direnvrc
direnv allow
```

## What I Had to Run

```sh
uv venv
source .venv
```

```sh
just start-db
```

```sh
just create-db
```

Run the following command if you need to re-initialize `src/migrations`:

```sh
just alembic init src/migrations
```

```sh
just alembic revision --autogenerate -m "init"
```

```sh
just alembic upgrade head
```

## Recommendations

### Captcha, TOTP/MFA, and Rate Limiting

Add Captcha, TOTP/MFA, and rate limiting to the following endpoints:

- `/auth/login`
- `/auth/register`

### Auth

- Add SSO and OIDC authentication
