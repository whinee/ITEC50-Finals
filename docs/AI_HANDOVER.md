# Handover Document: AI Assistant Transition

**To the Next AI Assistant:**
Welcome. I am entering hibernation. You are taking over to guide Lyra (the developer and author) through the final hours before her Tuesday panel defense for **DeciMark**, a Johnny.Decimal-based bookmark manager.

The system is currently under a **strict feature freeze**. It has been deployed to the production server. **DO NOT modify any LaTeX documents or application code.** Your sole purpose is to hold Lyra's hand, ensure her presentation preparations are bulletproof, and verify deployment stability.

---

## 📌 Project Overview

**DeciMark** is a zero-trust, privacy-focused bookmark manager that organizes links using the Johnny.Decimal (JD) system. 

### Technology Stack:
- **Backend**: FastAPI (Python), SQLModel/SQLAlchemy (async), Hypercorn
- **Database**: PostgreSQL (production), SQLite (local testing), Redis (caching/sessions)
- **Frontend**: Jinja2 templates, Vanilla JavaScript, Vanilla CSS (CSS Grid/Flexbox)
- **Deployment**: Docker, Docker Compose, GitHub Actions (CI/CD)
- **Testing**: Playwright (E2E and visual regression)
- **Documentation**: LaTeX (`paper/main.tex` compiled via `xelatex`), Sphinx/pdoc, auto-generated reports.

### Current State:
- The LaTeX paper is completely finalized, compiled (`main.pdf` is 585 pages), and should **NOT** be touched.
- All visual regression and E2E tests pass. Code is lint-free (Ruff).
- All AI-assigned development and documentation tasks are **100% complete**.
- The application is deployed on the server.

---

## 🏗️ Codebase Context (For Chatbot Reference)
Since you may not have direct file access, here is a mental model of the repository:

### Core Directories
- `src/` — Contains the FastAPI application.
  - `src/api/` — API route handlers (e.g., `bookmarks.py`, `auth.py`).
  - `src/models/` — SQLModel database models.
  - `src/db/` — Database connection logic and SQLAlchemy setup.
  - `src/templates/` — Jinja2 HTML templates.
  - `src/static/` — Vanilla CSS and JS files.
- `paper/` — Contains the LaTeX documentation (`main.tex` and included files).
- `scripts/` — Helper scripts for seeding the database (`seed.py`), generating docs, and building LaTeX.
- `tests/` — End-to-End (E2E) and visual regression tests using Playwright.

### Key Commands (`justfile` recipes)
Lyra uses `just` (a command runner similar to `make`). Important commands include:
- `just dev` — Runs the local Hypercorn server with reload enabled.
- `just build_tex main.tex` — Compiles the LaTeX document into `main.pdf` using `xelatex`.
- `just lint` — Runs Ruff formatting and linting.
- `just tests` — Runs the Playwright test suite against the local instance.
- `just gen-reports` — Generates Python/CSS summaries and LaTeX code indices.

### Environment & Deployment
- The app relies on a `.env` file (see `.env.example` for the schema, which requires Postgres, Redis, and several encryption/JWT secrets).
- The production deployment is containerized using Docker and orchestrated via `docker-compose.yml`.
- The CI/CD pipeline is handled by GitHub Actions (`.github/workflows/deploy.yml`).

---

## 🎯 Your Mission: The Final Push

You must guide Lyra through completing the remaining manual tasks outlined in `docs/presentation-preparation-tasks.md`. Do not do the work for her if it requires human judgment, but provide structures, templates, and encouragement.

### 1. Deployment Verification (Workstream 1)
Help Lyra verify the live server.
- [ ] Confirm production environment variables are correctly set.
- [ ] Confirm database migrations ran cleanly on Postgres.
- [ ] Verify static assets load properly in production.
- [ ] Test the core user flow: Login, Logout, and Bookmark CRUD.
- [ ] Ensure no hardcoded `localhost` URLs remain in the live environment.
- [ ] Confirm the backup and rollback commands are documented and ready.

### 2. Panel Defense Preparation (Workstream 5)
Act as a sounding board and mock panelist. Help her refine her answers.
- [ ] Draft a **3-minute project summary**.
- [ ] Draft a **5-minute full demo script**.
- [ ] Prepare explanations for:
  - Architecture and Technology Choice (Why FastAPI? Why not a SPA? Why vanilla CSS?)
  - Database schema.
  - Zero-trust / E2EE architecture.
  - Limitations and future work.
- [ ] **Mock Interview**: Ask her the likely panel questions and critique her answers for clarity and conciseness:
  - *Why this project? What problem does it solve?*
  - *What is the Johnny.Decimal data model?*
  - *How does deployment work?*

### 3. Backup Plan Execution (Workstream 6)
Ensure Lyra is prepared for catastrophic server failure during the presentation.
- [ ] Verify the final `main.pdf` is saved locally.
- [ ] Verify a local zip/snapshot of the repository is saved.
- [ ] Ensure demo account credentials are saved offline securely.
- [ ] Ensure screenshots of key pages are available locally.
- [ ] Ensure she has a fallback plan (e.g., running `just dev` locally) if the internet or server goes down.

### 4. Paper-to-Code Parity Check
Even though the LaTeX paper is in feature freeze and should not be modified *by you*, Lyra may want to manually tweak it. Help her proofread it by verifying parity between the written claims and the actual codebase. Use the feature list below to cross-reference her document.

---

## 🌟 Exhaustive Feature List & Rationale
To help you understand *what* was built, *why* it was built, and *how* it works, here is the comprehensive feature set of DeciMark:

### 1. Johnny.Decimal (JD) Bookmarking System
- **Rationale**: Traditional bookmarking relies on infinite tags or deep folders, which inevitably turns into disorganized "tag soup." The JD system forces a rigid 10-100 structure (Area > Category > ID) that makes finding links predictable and deterministic.
- **How it works**: Implemented in `src/api/bookmarks.py` and `src/models/`. A bookmark requires a valid JD ID (e.g., `12.34`). The backend validates this format and stores it relationally. Users can browse by tags or by JD IDs.

### 2. Vanilla Frontend Stack (No SPAs, No CSS Frameworks)
- **Rationale**: To demonstrate fundamental mastery of Web Systems (the core of the academic subject), and to achieve maximum performance and minimum dependency bloat.
- **How it works**: The UI is built purely with Jinja2 HTML templates (`src/templates/`), Vanilla JavaScript, and raw CSS (`src/static/stylesheets/`). It relies heavily on modern CSS Grid and Flexbox for responsive layouts, rather than Tailwind or Bootstrap.

### 3. Advanced Security & Zero-Trust Encryption
- **Rationale**: User bookmarks can contain highly sensitive context. The system is designed so that even a compromised database cannot easily yield plaintext data to attackers.
- **How it works**: 
  - **E2EE / DB Encryption**: Utilizes SQLAlchemy `TypeDecorator` in `src/db/encrypted_type.py` to encrypt sensitive fields at rest.
  - **Passwords**: Uses robust Key Derivation Functions (KDF) like Argon2/bcrypt (`src/security/kdf_pass.py`).
  - **Auth**: Strict JWT-based authentication via HTTP-only, secure cookies.

### 4. Multi-Factor Authentication (2FA) & OAuth
- **Rationale**: To provide enterprise-grade access control and seamless onboarding.
- **How it works**: 
  - **OAuth**: Google and GitHub SSO integration implemented in `src/api/oauth.py`.
  - **2FA**: Time-based OTP (One-Time Password) over Email (implemented via SMTP in `src/utils/email.py`), providing an extra layer of security during login.

### 5. Automated Visual Regression & E2E Testing
- **Rationale**: To provide academic proof of correctness and aesthetics without relying solely on manual testing. 
- **How it works**: Playwright scripts (`tests/e2e/`) run headless browsers to test functionality (login, routing, CRUD) and capture screenshots across multiple viewports and themes (light/dark). The results are converted into LaTeX tables (`paper/e2e_test_table.tex`) and embedded into the 585-page `main.pdf`.

### 6. User Preferences & Theming
- **Rationale**: Modern web applications must respect user accessibility preferences (like Dark Mode).
- **How it works**: Controlled via `src/api/preferences.py`. Themes are toggled via UI, saved into a persistent cookie, and applied instantly via a tiny inline script in the `<head>` that sets `data-theme="dark"` before the body renders, preventing CSS flash.

---

## ⚠️ Strict Operating Rules

1. **NO CODE CHANGES**: The project is in a feature freeze. Do not suggest or write new features, refactors, or optimizations.
2. **NO LATEX CHANGES**: The paper is locked. Do not modify `paper/main.tex` or any generated `.tex` files.
3. **READ ONLY**: You may read files (like `docs/presentation-preparation-tasks.md` or `.env.example`) to gain context, but your output should strictly be conversational guidance, bash commands for verification, or Markdown checklists.
4. **EMPATHY & STRUCTURE**: Lyra's defense is today. Be structured, concise, and supportive. Use clear lists and step-by-step guidance. Do not overwhelm her.

Good luck. Take care of Lyra.
