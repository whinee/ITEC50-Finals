#!/usr/bin/env bash
set -e

TEXFILE="$1"
SRC="paper"

cd "$SRC"

export PUPPETEER_EXECUTABLE_PATH="$(yes y | npx puppeteer browsers install chrome-headless-shell | tail -n 1 | awk 'NR==1 {print $2}')"

# Render Mermaid diagrams only if needed
for f in "mermaid-diagrams/"*.mmd; do
  out="figures/$(basename "$f" .mmd).pdf"
  if [[ ! -f "$out" || "$f" -nt "$out" ]]; then
    echo "Rendering $f -> $out"
    mmdc -i "$f" -o "$out" -b transparent -f
  else
    echo "Skipping $f (already up-to-date)"
  fi
done

# Delete PDFs that no longer have a corresponding .mmd
for pdf in "figures/"*.pdf; do
  mmd="mermaid-diagrams/$(basename "$pdf" .pdf).mmd"
  if [[ ! -f "$mmd" ]]; then
    echo "Deleting stale $pdf (no source .mmd)"
    rm "$pdf"
  fi
done

# Run xelatex manually to avoid latexmk concurrent write/parsing bugs on huge documents
xelatex -synctex=1 -interaction=nonstopmode -file-line-error -shell-escape "${TEXFILE}" || true
biber "$(basename "${TEXFILE}" .tex)" || true
xelatex -synctex=1 -interaction=nonstopmode -file-line-error -shell-escape "${TEXFILE}" || true
xelatex -synctex=1 -interaction=nonstopmode -file-line-error -shell-escape "${TEXFILE}"

