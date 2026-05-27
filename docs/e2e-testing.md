# E2E & Visual Testing Guide

Welcome to the comprehensive E2E testing framework for DeciMark! This suite leverages **Pytest** and **Playwright** to conduct incredibly rigorous UI interaction tests, full user authentication flows, automated Lighthouse auditing, and exhaustive cross-viewport visual regressions for the academic paper.

## 1. Prerequisites

Before running the tests, ensure your dependencies are fully synced and the Playwright browsers are installed:

```bash
uv sync
uv run playwright install chromium
```

You must also have a testing database seeded with at least one user (which the test suite logs in with). The scripts will automatically use credentials found in `seed_credentials.json`.

## 2. Running Standard E2E Tests

The core Pytest suite tests DOM state, cookie validation, modal behavior, and authentication flows without needing you to manually run the server.

To run the standard Pytest suite:

```bash
just tests e2e
```

Or run them directly via `uv`:

```bash
uv run pytest tests/e2e -v
```

This will automatically spin up a temporary Hypercorn server on port 4173 in the background, run the tests, and tear down the server.

## 3. Running Visual Regression & Lighthouse Audits

The visual regression suite is an absolute powerhouse. It iterates through the core application routes (`/`, `/login`, `/bookmarks`, etc.), taking screenshots of **both Light and Dark themes** across 7 different viewports ranging from `1920x1080` down to `320x640`.

It also runs Google Lighthouse against these routes to capture performance metrics.

To run the visual and performance testing suite:

```bash
uv run scripts/run_visual_tests.py
```

### Outputs

1. **Screenshots**: All generated visual captures are saved directly to `assets/static/images/screenshots/`, ready to be linked into your LaTeX paper or markdown documentation.
1. **LaTeX Manifests**:
   - `paper/e2e/pages.tex`: A completely auto-generated LaTeX file containing the formatted image references for every single screenshot captured.
   - `paper/e2e/lighthouse_reports.tex`: An auto-generated LaTeX file containing the tabular breakdown of Lighthouse scores (Performance, Accessibility, Best Practices, SEO) for every tested page.

## Troubleshooting

- **Address already in use**: If the Pytest suite or visual tests fail to start because port `4173` is busy, ensure you don't have a background dev server running.
- **Lighthouse not found**: Ensure you have Node.js installed and can run `npx lighthouse` globally, as the Python script delegates to the Lighthouse CLI.
