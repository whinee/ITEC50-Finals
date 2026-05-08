# DeciMark

## Initial setup

Requires [direnv](https://direnv.net/).

```bash
mkdir -p ~/.config/direnv
# Either copy or append the layout script
cat .direnv.uv >> ~/.config/direnv/direnvrc
direnv allow
```

```sh
uv venv
source .venv
```

```sh
alembic init src/migrations
```

```sh
ENV=development uv run alembic revision --autogenerate -m "init"
```