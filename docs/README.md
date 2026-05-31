# DeciMark

DeciMark is a server-rendered bookmark manager built around Johnny.Decimal identifiers, tags, and user-owned bookmark records.

## Stack

- **FastAPI** — request routing, dependency injection, and API endpoints. Chosen for its raw ASGI performance, built-in Pydantic validation, and automatic OpenAPI schema generation.
- **SQLModel** — shared database and schema models. Allows utilizing the power of SQLAlchemy while writing concise Pydantic-compatible type hints.
- **PostgreSQL** — durable relational storage and many-to-many bookmark relations. Provides ACID compliance and robust relational integrity.
- **Jinja2** — server-rendered HTML pages. Allows zero-JS functional baseline rendering for ultimate resilience.
- **Vanilla JavaScript** — progressive enhancement without a client SPA framework. Keeps the application hyper-lightweight by executing interactivity strictly via raw DOM manipulation and the Fetch API, sidestepping heavy client-side bundle costs.
- **Hypercorn** — ASGI server used by `just dev` and `just run`. Selected for HTTP/2 support and high asynchronous throughput.
- **Playwright** — browser automation for visual and end-to-end checks. Provides cross-browser rendering accuracy for UI regression testing.
- **Docker Compose** — local Postgres and Redis orchestration. Eliminates manual binary dependencies for local development.

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

The application relies on the following environment variables, detailed in `.env.example`:

### Server & App Config

| Variable | Purpose |
| --- | --- |
| `ENV` | Environment mode (e.g., `production`, `development`). |
| `DEBUG` | Enables debugging features when `true`. |
| `HOST` / `PORT` | Bind address and port for the application server. |
| `WORKERS` | Number of Uvicorn/Hypercorn workers to run. |
| `ORIGINS` | Comma-separated list of allowed CORS origins. |
| `API_ROOT` | The root path for backend API routes (e.g., `/api`). |

### PostgreSQL Database

| Variable | Purpose |
| --- | --- |
| `PG__HOST` / `PG__PORT` | Database host and port. |
| `PG__USER` / `PG__PASSWORD` | Database credentials. |
| `PG__DBNAME` | Name of the primary application database. |
| `PG_SYNC_URL` / `PG_ASYNC_URL` | SQLAlchemy connection URIs (usually derived automatically). |
| `PG_DATA` | Local mount path for the Docker PostgreSQL data volume. |
| `EXTERNAL_DB_PORT` | Port exposed to the host for external DB connection. |

### Redis & Caching

| Variable | Purpose |
| --- | --- |
| `REDIS_URL` | Connection URL for the Redis server. |
| `REDIS_DATA` | Local mount path for the Docker Redis data volume. |
| `EXTERNAL_REDIS_PORT` | Port exposed to the host for external Redis connection. |
| `EXTERNAL_WEB_PORT` | Port exposed to the host for the web server. |

### Security & Cryptography

| Variable | Purpose |
| --- | --- |
| `AUTH__JWT_SECRET` | Secret key for signing JSON Web Tokens. |
| `AUTH__COOKIE_SECRET` | Secret key for encrypting HTTP-only cookies. |
| `AUTH__WEBHOOK_SECRET` | Secret key for validating incoming webhooks. |
| `AUTH__DB_ENCRYPTION_KEY` | Secret key for encrypting sensitive data at rest in PostgreSQL. |

### Testing

| Variable | Purpose |
| --- | --- |
| `TEST__DBNAME` | Name of the database used exclusively for testing. |
| `TEST__LIGHTHOUSE` | Enables Lighthouse performance auditing during tests. |
| `TEST__SMTP` | Toggles SMTP functionality in the testing environment. |

### SMTP (Email)

| Variable | Purpose |
| --- | --- |
| `SMTP__HOST` / `SMTP__PORT` | Mail server host and port. |
| `SMTP__USERNAME` / `SMTP__PASSWORD` | Mail server authentication credentials. |

### OAuth Providers

| Variable | Purpose |
| --- | --- |
| `OAUTH__GOOGLE__ENABLE` | Toggles Google OAuth integration. |
| `OAUTH__GOOGLE__CLIENT_ID` / `_SECRET` | Google OAuth application credentials. |
| `OAUTH__GITHUB__ENABLE` | Toggles GitHub OAuth integration. |
| `OAUTH__GITHUB__CLIENT_ID` / `_SECRET` | GitHub OAuth application credentials. |

## AI Disclosure

In the interest of academic integrity, the following discloses the use of artificial intelligence tools during the development of this project. The initial codebase, comprising approximately 35,000 to 40,000 lines of code, was authored by the author with foundational assistance from OpenAI Codex and Anthropic's Claude AI, alongside properly licensed third-party assets (such as Swagger UI CSS and open-source snippets from authors like uncomfyhalomacro). Subsequently, an advanced AI coding assistant was utilized as a pair-programming accelerator under the author's explicit instruction and supervision to scale the project to its current 45,000 lines of code. All architectural decisions, design choices, and implementation strategies were conceived, directed, and validated by the author. AI tools were used as assistive accelerators — not as a substitute for understanding.

- **HTML Templates**: The Jinja2 template files under `src/templates/bookmarks` were initially scaffolded with assistance from OpenAI Codex, and subsequently reviewed, corrected, and heavily modified by the author to conform to the application's architecture.
- **Utility Scripts**: Several Python scripts in the `scripts/` directory were drafted with Anthropic's Claude AI as a starting point, with the author directing the logic, reviewing the output, and rewriting where necessary.
- **Documentation sync and Error fixing**: Accelerated with AI pair-programming under the author's direction to split the presentation tasks between the author and AI, and fixed D103 and D401 Ruff docstring errors across the main app and scripts.
- **Dependency and Technical Debt Cleanup**: Accelerated with AI pair-programming under the author's direction, resolving FastAPI deprecation warnings by replacing `UJSONResponse` with `JSONResponse`, removing deprecated dependencies like `ujson` from `pyproject.toml`, and adding proper `CORSMiddleware` configuration using the `ORIGINS` environment variable to restrict domain access.
- **Mobile Viewport Optimization**: Rectified a layout overflow issue on the landing page CSS specifically targeting 320px ultra-narrow screens by tuning CSS Grid `minmax` logic and `clamp()` typography variables.
- **Deployment & Test Stability**: Engineered robust deployment capabilities under the author's direction by defining scaling configurations (`WORKERS` limits) for Hypercorn, standardizing Docker Compose environment mappings to avoid schema loss in PostgreSQL during ephemeral restarts, and tuning the automated seeding script to gracefully adapt database population sizes for stability in testing.

The overall system architecture, the Johnny.Decimal integration model, the zero-trust security design, the CSS design system, the JavaScript interaction logic, the database schema, the deployment strategy, and the substantive content of the reflection and rationale were authored entirely by the author. The use of AI tools did not substitute for technical understanding; it accelerated execution of decisions already made.
