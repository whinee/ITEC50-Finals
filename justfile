# regex to match recipe names and their comments:
# ^    (?P<recipe>\S+)(?P<args>(?:\s[^#\s]+)*)(?:\s+# (?P<docs>.+))*

# Choose recipes
default:
    @ just -lu

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

[private]
nio_dev:
    @ python -m no_implicit_optional dev; exit 0

[private]
nio_src:
    @ python -m no_implicit_optional src; exit 0

[private]
ruff:
    @ python -m ruff check src --fix; exit 0

# Set up development environment
[unix]
bootstrap:
    #!/usr/bin/env bash
    rm -rf .venv
    rm -f uv.lock
    uv venv
    source .venv/bin/activate
    uv sync

# Set up development environment
[windows]
bootstrap:
    Remove-Item -Recurse -Force .venv
    Remove-Item -Force uv.lock
    uv venv
    . .\.venv\Scripts\Activate.ps1
    uv sync

# Lint codebase
lint:
    just nio_dev
    just nio_src
    python -m mdformat docs
    python -m black -q .
    just ruff

# Run web app
run:
    ENV=development hypercorn main:app --reload --bind 0.0.0.0:8000 --workers 16

# Run web app in a lightweight way
dev:
    ENV=development hypercorn main:app --reload --bind 0.0.0.0:8000 --workers 1
