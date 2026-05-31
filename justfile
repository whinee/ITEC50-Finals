# regex to match recipe names and their comments:
# ^    (?P<recipe>\S+)(?P<args>(?:\s[^#\s]+)*)(?:\s+# (?P<docs>.+))*

set dotenv-load := true
set shell := ["bash", "-cu"]

export PG_SYNC_URL := "postgresql+psycopg://" + env_var_or_default("PG__USER", "postgres") + ":" + env_var_or_default("PG__PASSWORD", "postgres") + "@localhost:" + env_var_or_default("EXTERNAL_DB_PORT", "5432") + "/" + env_var_or_default("PG__DBNAME", "decimark")
export PG_ASYNC_URL := "postgresql+psycopg_async://" + env_var_or_default("PG__USER", "postgres") + ":" + env_var_or_default("PG__PASSWORD", "postgres") + "@localhost:" + env_var_or_default("EXTERNAL_DB_PORT", "5432") + "/" + env_var_or_default("PG__DBNAME", "decimark")
export REDIS_URL := "redis://localhost:" + env_var_or_default("EXTERNAL_REDIS_PORT", "6379") + "/0"

# Choose recipes
default:
    @ just -l

optimize_images:
    bash optimize_images.sh 

gen_blog:
    node blog.js

screenshot:
    CHROME_PATH="/usr/bin/ungoogled-chromium" node screenshot.js

build_tex doc:
    latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error -bibtex -shell-escape "{{doc}}"

build:
    just optimize_images
    just gen_blog
    just screenshot
    just build_tex main.tex

tests +args="":
    uv run pytest {{args}}

test-migrations:
    just stop-db || true
    just start-db
    just create-test-db
    PG__DBNAME=${TEST__DBNAME:-decimark_test} uv run alembic upgrade head
    PG__DBNAME=${TEST__DBNAME:-decimark_test} uv run alembic downgrade base
    just drop-test-db

alembic +args:
    uv run alembic {{args}}

stop-redis:
    docker compose stop redis || true

start-redis:
    just stop-redis
    docker compose up -d redis

stop-db:
    docker compose stop db || true

start-db:
    just stop-db
    docker compose up -d db

create-db-user:
    docker compose exec -T db createuser -s ${PG__USER} || true

create-db:
    docker compose exec -T db psql -U ${PG__USER} \
        -tc "SELECT 1 FROM pg_database WHERE datname='${PG__DBNAME}'" | \
        grep -q 1 || \
    docker compose exec -T db psql -U ${PG__USER} \
        -c "CREATE DATABASE ${PG__DBNAME};"

drop-db:
    docker compose exec -T db psql -U ${PG__USER} \
        -c "DROP DATABASE IF EXISTS ${PG__DBNAME};"

create-test-db:
    docker compose exec -T db psql -U ${PG__USER} \
        -tc "SELECT 1 FROM pg_database WHERE datname='${TEST__DBNAME}'" | \
        grep -q 1 || \
    docker compose exec -T db psql -U ${PG__USER} \
        -c "CREATE DATABASE ${TEST__DBNAME};"

drop-test-db:
    docker compose exec -T db psql -U ${PG__USER} \
        -c "DROP DATABASE IF EXISTS ${TEST__DBNAME};"

[private]
nio_scripts:
    @ uv run no_implicit_optional scripts; exit 0

[private]
nio_src:
    @ uv run no_implicit_optional src; exit 0

[private]
ruff_scripts:
    @ uv run ruff check scripts --fix; exit 0

[private]
ruff_src:
    @ uv run ruff check src --fix; exit 0

# Lint JS files
[private]
lint-js:
    @ npx prettier "src/static/scripts/**/*.js" --tab-width 4 --write; exit 0

# Lint CSS files
[private]
lint-css:
    @ uv run scripts/summarize_css.py

# Lint CSS files
[private]
format-css:
    @ npx prettier "src/static/stylesheets/**/*.css" --tab-width 4 --write; exit 0
    @ just lint-css

# Lint HTML files
[private]
lint-html:
    @ npx --yes hint src/templates/**/*.j2.html src/templates/*.j2.html --formatters summary; exit 0

# Lint Jinja2 templates
[private]
lint-jinja:
    @ uv run djlint ./src/templates --reformat --quiet; exit 0

# Lint Markdown files
[private]
lint-md:
    @ uv run mdformat docs

# Lint Jinja2 templates
[private]
lint-tex:
    @ tex-fmt paper --recursive --nowrap

# Lint codebase
lint:
    just nio_scripts
    just nio_src
    just ruff_scripts
    just ruff_src
    uv run black -q scripts
    uv run black -q src
    just lint-js
    just lint-css
    just lint-html
    just lint-jinja
    just lint-md
    just lint-tex

# Seed data
seed:
    uv run scripts/seed.py

[private]
restart-web-deps:
    just start-db
    just start-redis

# Generate reports
gen-reports:
    @ just restart-web-deps
    @ just lint-css
    @ uv run scripts/summarize_python.py
    @ uv run scripts/generate_scc_report.py --count-as 'j2.html:Jinja2'
    @ uv run scripts/run_visual_tests.py
    @ just lint-tex
    @ just lint-md

# Run web app in a lightweight way
dev:
    just restart-web-deps
    uv run hypercorn main:app --reload --bind 0.0.0.0:8000 --workers 1

# Run web app
run:
    just restart-web-deps
    uv run hypercorn main:app --reload --bind 0.0.0.0:8000 --workers 16
