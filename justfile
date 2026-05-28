# regex to match recipe names and their comments:
# ^    (?P<recipe>\S+)(?P<args>(?:\s[^#\s]+)*)(?:\s+# (?P<docs>.+))*

set dotenv-load := true
set shell := ["bash", "-cu"]

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
    #!/bin/sh
    echo "stopping any existing instance"
    just stop-db || true
    echo "Starting test postgres server with ${PG_DATA}"
    just start-db
    just create-test-db
    just alembic upgrade head
    just alembic downgrade base
    echo "Cleaning up"
    just stop-db
    rm -rf "${PG_DATA}"
    echo "Stopped postgres server. Do not forget to run start-db with your own PG_DATA to restart"

alembic +args:
    uv run alembic {{args}}

stop-redis:
    docker stop decimark-redis || true
    docker rm decimark-redis || true

start-redis:
    mkdir -p "${REDIS_DATA}"
    just stop-redis
    docker run -d --name decimark-redis -p 6379:6379 -v "${PWD}/${REDIS_DATA}:/data" redis:alpine || docker start decimark-redis

start-db:
    if [ ! -f "${PG_DATA}/PG_VERSION" ]; then initdb -D "${PG_DATA}" -U ${PG__USER}; fi
    sed -i -E "s/#unix_socket_directories = '\/var\/run\/postgresql, \/tmp' # comma-separated list of directories/unix_socket_directories = '\/tmp' # comma-separated list of directories/" "${PG_DATA}/postgresql.conf"
    pg_ctl -o "${INIT_DB_OPTIONS}" -D "${PG_DATA}" start

stop-db:
    pg_ctl -D ${PG_DATA} stop

create-db-user:
    createuser -s ${PG__USER}

create-db:
    psql -h ${PG__HOST} -p ${PG__PORT} -U ${PG__USER} \
        -tc "SELECT 1 FROM pg_database WHERE datname='${PG__DBNAME}'" | \
        grep -q 1 || \
    psql -h ${PG__HOST} -p ${PG__PORT} -U ${PG__USER} \
        -c "CREATE DATABASE ${PG__DBNAME};"

drop-db:
    psql -h ${PG__HOST} -p ${PG__PORT} -U ${PG__USER} \
        -c "DROP DATABASE IF EXISTS ${PG__DBNAME};"

create-test-db:
    psql -h ${PG__HOST} -p ${PG__PORT} -U ${PG__USER} \
        -tc "SELECT 1 FROM pg_database WHERE datname='${TEST__DBNAME}'" | \
        grep -q 1 || \
    psql -h ${PG__HOST} -p ${PG__PORT} -U ${PG__USER} \
        -c "CREATE DATABASE ${TEST__DBNAME};"

drop-test-db:
    psql -h ${PG__HOST} -p ${PG__PORT} -U ${PG__USER} \
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
    @ npx htmlhint "**/*.html"; exit 0

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
    # just lint-html
    just lint-jinja
    just lint-md
    just lint-tex

# Generate reports
gen-reports:
    @ just lint-css
    @ uv run scripts/summarize_python.py
    @ uv run scripts/generate_scc_report.py --count-as 'j2.html:Jinja2'
    @ uv run scripts/run_visual_tests.py
    @ just lint-tex
    @ just lint-md

# Seed data
seed:
    uv run scripts/seed.py

# Run web app in a lightweight way
dev:
    just stop-db || true
    just stop-redis || true
    just start-db
    just start-redis
    hypercorn main:app --reload --bind 0.0.0.0:8000 --workers 1

# Run web app
run:
    hypercorn main:app --reload --bind 0.0.0.0:8000 --workers 16
