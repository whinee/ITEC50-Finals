# DeciMark

DeciMark is an experimental bookmark manager leveraging the structural rigor of Johnny.Decimal (J.D). It treats links not just as URLs to save for later, but as codified information assets mapped to a defined system.

Built with Python, Starlette/FastAPI, SQLAlchemy, and minimal vanilla JavaScript, DeciMark enforces strict organization while providing high-performance access to your digital bibliography.

> The aspiration to do great things are paved by small yet well-built tools.

## Key Features

- **Johnny.Decimal Integration**: Every bookmark is rigorously categorized using J.D node architectures.
- **Advanced Tagging & Context**: Freeform tagging with dynamic color associations and markdown-enabled notes.
- **Zero-Trust Storage Base**: Optional deployment-level symmetric encryption of bookmarks using AEAD configurations.
- **Glassmorphic UI**: High-contrast, dynamic, and responsive visual experience built from the ground up without heavy frontend frameworks.
- **Asynchronous & Concurrent Processing**: Fully async backend via Uvicorn for handling bulk data operations and simultaneous client connections efficiently.
- **OAuth 2.0 Integration**: Supports logging in via Google and GitHub with automatic dynamic endpoint and UI toggling based on configuration presence.
- **Two-Factor Authentication**: Enforces email-based, short-lived, rate-limited One-Time Passwords (OTP) on top of the base authentication flow.

## Local Development and Infrastructure Setup

Ensure you have Python 3.12 or newer installed. This project requires `just` as a command runner.

```bash
# Set up the virtual environment and install dependencies
just venv
source .venv/bin/activate
just install

# Run database migrations and populate the initial structure
just migrate
```

To run the primary development server:

```bash
just run
```

### Visual Testing and Modals

DeciMark includes automated E2E tests built using Playwright, designed to ensure critical visual components, such as authentication modals, render flawlessly across viewports.

To execute the screenshot automation suite:

```bash
just test-modals
```

Screenshots are generated and deposited into `docs/visuals/`.

## The Johnny.Decimal Philosophy in DeciMark

The core organizational principle of DeciMark revolves around the Johnny.Decimal system. This differs from traditional, chaotic, tag-based bookmarking by forcing constraints.

A bookmark must belong to a structural node: `Area -> Category -> ID`.

For example, `11.11` belongs to Area 10-19, Category 11, ID 11. By forcing links into strict categorical silos *before* allowing loose tagging, DeciMark attempts to solve digital hoarding by making retrieval deterministic.

## Configuration & Environment Variables

DeciMark utilizes `.env` for overriding operational behaviors. The following variables are significant for testing and development:

- `TEST__NO_AUTH`: When set to `True`, disables authentication middleware globally.
- `TEST__NO_2FA`: When set to `True`, bypasses the 2FA requirement after login.
- `TEST__LIGHTHOUSE`: Boolean flag to trigger CI performance audits.
- `TEST__SMTP`: When set to `True`, intercepts outgoing emails and logs OTPs directly to the console for frictionless local testing.

### External Integrations (MFA & OIDC)

- `SMTP__HOST`, `SMTP__PORT`, `SMTP__USERNAME`, `SMTP__PASSWORD`: Configures the outbound SMTP relay for dispatching 2FA verification codes.
- `OAUTH__GOOGLE_CLIENT_ID`, `OAUTH__GOOGLE_CLIENT_SECRET`: Credentials for Google SSO.
- `OAUTH__GITHUB_CLIENT_ID`, `OAUTH__GITHUB_CLIENT_SECRET`: Credentials for GitHub SSO.

## AI Disclosure

In the interest of academic integrity, the following discloses the use of artificial intelligence tools during the development of this project. The initial codebase, comprising approximately 35,000 to 40,000 lines of code, was authored by the author with foundational assistance from OpenAI Codex and Anthropic's Claude AI, alongside properly licensed third-party assets (such as Swagger UI CSS and open-source snippets from authors like uncomfyhalomacro). Subsequently, an advanced AI coding assistant was utilized as a pair-programming accelerator under the author's explicit instruction and supervision to scale the project to its current 45,000 lines of code. All architectural decisions, design choices, and implementation strategies were conceived, directed, and validated by the author. AI tools were used as assistive accelerators — not as a substitute for understanding.

- **HTML Templates**: The Jinja2 template files under `src/templates/bookmarks` were initially scaffolded with assistance from OpenAI Codex, and subsequently reviewed, corrected, and heavily modified by the author to conform to the application's architecture.

- **Utility Scripts**: Several Python scripts in the `scripts/` directory were drafted with Anthropic's Claude AI as a starting point, with the author directing the logic, reviewing the output, and rewriting where necessary.

- **Advanced Security Engineering**: The zero-trust E2EE architecture via `sqlalchemy-utils` Fernet TypeDecorators, the asynchronous OAuth 2.0 integration for Google and GitHub, and the dual-state SMTP/2FA routing were accelerated with AI pair-programming under the author's direction.

- **Base64 JSON Theme State**: The lightweight Base64 import/export marketplace logic for tags was scaffolded using AI tools, then heavily refactored by the author for strict Pydantic parsing.

- **Backend & Frontend Modifications**: Google DeepMind's Antigravity was used as an assistive pair-programming tool to accelerate implementation of specific features under the author's direction, including:

  - The `edit` bookmark endpoint and associated frontend logic in `src/api/bookmarks.py` and `bookmarks.js`.
  - Authentication tightening and the `/login` auto-redirect endpoint.
  - Hamburger menu styling and the SVG `mask-image` icon theming technique.
  - CSS accessibility improvements replacing hardcoded colors with theme variables.
  - Refactoring of frontend forms and backend API payloads to support multiple JD IDs per bookmark.
  - The `scripts/seed.py` bulk-insert pipeline rewrite.
  - The glassmorphic landing page (`index.j2.html`).
  - Client-side UTC-to-local timezone conversion and skeleton loading states.
  - E2E test suite concurrency refactoring in `scripts/run_visual_tests.py`.
  - Resolution of the `/bookmarks/jd` and `/bookmarks/tag` load button logic.
  - Integration of the `favicon.svg` branding logo across all pages via the unified `base.j2.html` header and bookmark dashboard titles.
  - Implementation of `@media (prefers-color-scheme: dark)` media queries in `favicon.svg` and `favicon-not-safe.svg` to support OS-level dark mode switching.
  - Implementation and refinement of a dark mode gradient title page design in LaTeX using TikZ and PGF radial shadings for smoother, more granular visual transitions.
  - Refactoring of `scripts/summarize_css.py` to concatenate all CSS summary documentation into a single LaTeX index file, streamlining document compilation.
  - Creation of `scripts/summarize_python.py` to parse Python module docstrings via `pdoc3` and convert them to LaTeX using `pypandoc` for inclusion in the final document.
  - Resolution of cryptographic payload formatting in the `jwt_service.sign` method for standardized authentication.
  - Rectification of PostgreSQL strict schema validation errors during the automated provisioning of Demo Mode accounts.
  - Implementation of an inline, high-performance database seeder within the `/auth/demo` endpoint, utilizing raw `sqlalchemy.insert` commands to instantaneously provision 10,000 randomized bookmarks, 100 tags, and 100 Johnny.Decimal nodes for immediate friction-free demonstration.
  - Engineering of a comprehensive, cascade-delete teardown protocol inside the `/logout` route, guaranteeing zero-trust data hygiene by securely incinerating all generated artifacts and the demo account itself upon session termination. To prevent UI blocking, this deletion was shifted into an asynchronous Starlette `BackgroundTask`.
  - Development of `scripts/cleanup_demos.py`, an external, cron-ready CLI utility designed to automatically sweep the database and aggressively purge any demo accounts that have remained inactive for over 60 minutes.
  - Refactoring of the Pydantic settings schema to introduce deeply nested OAuth enablement flags (`settings.OAUTH.GOOGLE.ENABLE`), securely passing the global settings object into the Jinja2 template context (`TEMPLATES.env.globals`) to dynamically strip unconfigured OAuth provider buttons from the DOM and enforce hard 404 blocks on deactivated callback routes.
  - Comprehensive refactoring of Jinja2 HTML templates (`login.j2.html`, `register.j2.html`, `2fa.j2.html`, `public_docs.j2.html`, `base.j2.html`, `tag.j2.html`, `edit.j2.html`) to systematically eliminate all inline `style="..."` attributes and meticulously abstract them into semantic CSS utility classes across the standard stylesheet matrix (`forms.css`, `base.css`, `bookmarks.css`, `landing.css`).

- **Backend Docstrings**: Google-style docstrings across the backend Python modules were authored with AI assistance to meet documentation standards.

- **Frontend Modals & Splash UI**: Developed robust Playwright E2E tests for modal interactions with automated screenshotting. Engineered dynamic Jinja2 injection of randomized splash quotes on authentication views via Python route extensions.

- **Documentation Integration**: Injected an automated public documentation viewer route mapping directly to README metrics, updated the core README to distinctly explain the Johnny.Decimal design philosophy of DeciMark, and aggressively sanitized pdoc3 LaTeX artifacts to remove auto-generated signatures.

- **Rapid Prototyping & QA Automation**: Accelerated the execution of numerous backlog tasks (e.g., automated seeding with randomized Epoch dates, toggleable password visibility scripts, UI/CSS polishing for erase-input, instantaneous feedback modal integration, frontend username generation, and secure DB checks for stale authentication tokens).

- **Demo Auto-Provisioning**: Engineered a dedicated, highly robust demo login route ensuring immediate, friction-free access to a populated dashboard via dynamically generated users and symmetric JWT signing.

- **Advanced Security Architecture**: Engineered a zero-trust backend by integrating Redis-backed rate limiting via `fastapi-limiter` on all authentication endpoints, and built a native, self-hosted visual CAPTCHA generation engine using Python to aggressively thwart automated brute-force attacks without relying on third-party tracking APIs.

- **Paper Sections**: Certain sections of `paper/main.tex` were drafted collaboratively with AI assistance and then edited by the author, including:

  - The HSL Color Strategy section, the navigation flow TikZ diagram, the Lighthouse Audit appendix, and the Theoretical Foundations chapter.
  - The Abstract, Acknowledgements, and the restructuring of the Dedication into three typographically distinct pages.

- **Dynamic Frontend Theming**: Authored a robust HSL color manipulation pipeline within `bookmarks.js` that reads custom hex values from the newly exposed `/api/tags` endpoint, calculates mathematically contrasting foreground/background ratios, and injects them directly into CSS Custom Properties for flawless custom Tag rendering.

The overall system architecture, the Johnny.Decimal integration model, the zero-trust security design, the CSS design system, the JavaScript interaction logic, the database schema, the deployment strategy, and the substantive content of the reflection and rationale were authored entirely by the author. The use of AI tools did not substitute for technical understanding; it accelerated execution of decisions already made.
