# DeciMark

DeciMark is a server-rendered bookmark manager built around Johnny.Decimal identifiers, tags, and user-owned bookmark records.

## Stack

- **FastAPI** — request routing, dependency injection, and API endpoints.
- **SQLModel** — shared database and schema models.
- **PostgreSQL** — durable relational storage and many-to-many bookmark relations.
- **Jinja2** — server-rendered HTML pages.
- **Vanilla JavaScript** — progressive enhancement without a client SPA framework.
- **Hypercorn** — ASGI server used by `just dev` and `just run`.
- **Playwright** — browser automation for visual and end-to-end checks.
- **Docker Compose** — local Postgres and Redis orchestration.

## Setup

Use the real repository commands:

```bash
just start-db
just start-redis
just tests
just lint
just gen-reports
just dev
```

For the main app server:

```bash
just run
```

For migrations:

```bash
just alembic upgrade head
```

For test database migration checks:

```bash
just test-migrations
```

## Runtime dependencies

`just dev` and `just run` expect Docker Compose services for:

- PostgreSQL
- Redis

The lint and report recipes also depend on external tools installed in the environment:

- `uv`
- `black`
- `ruff`
- `djlint`
- `mdformat`
- `tex-fmt`
- `npx`
- `latexmk`
- `playwright`
- `hypercorn`

## Justfile recipe reference

### Public recipes

| Recipe | Purpose | Dependencies |
| --- | --- | --- |
| `default` | Lists available recipes | none |
| `optimize_images` | Runs `scripts/optimize_images.sh` | shell utilities |
| `gen_blog` | Runs `node blog.js` | Node.js, project script |
| `screenshot` | Runs `node screenshot.js` with Chromium path set | Node.js, Chromium, project script |
| `build_tex doc` | Builds the selected LaTeX file with `latexmk` | `latexmk`, XeLaTeX, BibTeX |
| `build` | Runs image optimization, blog generation, screenshots, and paper build | all build dependencies |
| `tests +args=""` | Runs the pytest suite through `uv` | `uv`, pytest |
| `test-migrations` | Verifies Alembic upgrade/downgrade on a test database | Docker Compose, Alembic |
| `alembic +args` | Runs Alembic commands through `uv` | `uv`, Alembic |
| `stop-redis` | Stops Redis in Docker Compose | Docker Compose |
| `start-redis` | Restarts Redis in Docker Compose | Docker Compose |
| `stop-db` | Stops PostgreSQL in Docker Compose | Docker Compose |
| `start-db` | Restarts PostgreSQL in Docker Compose | Docker Compose |
| `create-db-user` | Creates the database superuser in the DB container | Docker Compose, `psql` |
| `create-db` | Creates the main application database if missing | Docker Compose, `psql` |
| `drop-db` | Drops the main application database | Docker Compose, `psql` |
| `create-test-db` | Creates the test database if missing | Docker Compose, `psql` |
| `drop-test-db` | Drops the test database | Docker Compose, `psql` |
| `lint` | Runs Python, CSS, JS, HTML, Jinja2, Markdown, and TeX linting/formatting | tools listed above |
| `seed` | Seeds demo data | `uv`, `scripts/seed.py` |
| `gen-reports` | Regenerates CSS/Python summaries, SCC report, visual tests, and docs/TeX lint outputs | Docker Compose, `uv`, `tex-fmt`, Playwright |
| `dev` | Starts app with reload on port 8000 | Docker Compose, `uv`, Hypercorn |
| `run` | Starts app with reload and 16 workers on port 8000 | Docker Compose, `uv`, Hypercorn |

### Private helper recipes

These recipes are internal support only and are not part of the public operator surface:

- `nio_scripts`
- `nio_src`
- `ruff_scripts`
- `ruff_src`
- `lint-js`
- `lint-css`
- `format-css`
- `lint-html`
- `lint-jinja`
- `lint-md`
- `lint-tex`
- `restart-web-deps`

## Environment variables

Key runtime variables:

- `PG__USER`
- `PG__PASSWORD`
- `PG__DBNAME`
- `EXTERNAL_DB_PORT`
- `EXTERNAL_REDIS_PORT`
- `TEST__DBNAME`
- `TEST__NO_AUTH`
- `TEST__NO_2FA`
- `TEST__LIGHTHOUSE`
- `TEST__SMTP`
- `SMTP__HOST`
- `SMTP__PORT`
- `SMTP__USERNAME`
- `SMTP__PASSWORD`
- `OAUTH__GOOGLE__ENABLE`
- `OAUTH__GOOGLE__CLIENT_ID`
- `OAUTH__GOOGLE__CLIENT_SECRET`
- `OAUTH__GITHUB__ENABLE`
- `OAUTH__GITHUB__CLIENT_ID`
- `OAUTH__GITHUB__CLIENT_SECRET`

## Paper sync note

Paper text should stay aligned with the implementation and the command surface above.

If command names change, update this file and `paper/main.tex` together.
