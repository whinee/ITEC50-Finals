---
marp: true
theme: default
class:
  - lead
paginate: true
backgroundColor: #131320
color: #e0e0e0
style: |
  h1 { color: #F173AC; font-family: 'Arial', sans-serif; }
  h2 { color: #a68cd9; font-weight: normal; }
  strong { color: #F173AC; }
  a { color: #a68cd9; }
  ul li { font-size: 1.2rem; line-height: 1.8; text-align: left; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
---

<!-- markdownlint-disable MD024 MD025 -->

# DeciMark: A Johnny.Decimal Bookmark Manager

**Lyra Phasma** | ITEC50 Final Project

*An Individual Submission for the "Full-Stack Concepts" MVP* <!-- markdownlint-disable-line MD036 -->

---

# Phase 1: Research & Requirements

## The Void in Bookmark Management

- **Pinboard:** Minimalist, flat tags, visually dead.
- **Raindrop.io:** Visually rich, heavily nested, lacks structural discipline.
- **DeciMark's Solution:** Enforcing the Johnny.Decimal numeric classification system (Area > Category > ID) natively.

---

# Phase 2: Design & The Cascade (CSS)

## Algorithmic Layouts & The Box Model

- **CSS Grid:** Used `repeat(auto-fill, minmax(280px, 1fr))` for a fluid, breakpoint-free dashboard layout.
- **Flexbox:** Used for single-axis alignment (navigation, card metadata).
- **Box Model:** Global `box-sizing: border-box` to prevent padding/margins from breaking flex alignments.

---

# Phase 2: Specificity & Inheritance

## Overcoming Cascade Conflicts

- **The Challenge:** Styling the SVG icon system globally, while allowing contextual overrides.
- **The Solution:** A base `.svg-icon` class (low specificity), overridden by a contextual selector `.bookmark-card .icon-delete` to safely change the `background-color` without resorting to `!important`.

---

# Phase 3: Media Optimization & Typography

## Vector Exclusivity & Zero-Trust Fonts

- **SVG Engine:** Zero raster images. Icons are injected via the CSS `mask-image` property.
- **HSL Theming:** Light/Dark mode is achieved by adjusting *only* the Lightness variable in CSS custom properties.
- **Local Typography:** Built a custom Python pipeline to compile TrueType fonts into ultra-compressed WOFF2 binaries. Zero reliance on Google Fonts.

---

# Phase 4: System Logic (JavaScript)

## Data Handling & DOM Output

- **Reference Types:** Client-side state is a module-scoped Array of Bookmark objects.
- **Conditional Logic & Loops:** `Array.prototype.filter()` evaluates the active state, feeding a `for...of` loop to render the UI.
- **DOM Output:** Raw `document.createElement()` dynamically builds cards, strictly bypassing `innerHTML` to prevent XSS.

---

# Reflection: Client-Server & The Cascade

- **Client-Server Reality:** Built a *Pessimistic UI*. Deleting a bookmark doesn't immediately remove it—it dispatches an HTTP request. The UI only updates when the server confirms a 204 No Content status.
- **Cascade Conflict:** Managing CSS variable updates for dark mode. Solved by injecting the theme state directly into the `<html>` element via Jinja2 before the first paint to prevent CSS flashing.

---

# PART II: BACKEND ARCHITECTURE

*Moving beyond the rubric into Enterprise Engineering* <!-- markdownlint-disable-line MD036 -->

---

# Zero-Trust Cryptography

## An Impenetrable Authentication Layer

- **Argon2id:** Passwords subjected to memory-hard key derivation to resist GPU brute-forcing.
- **Double-Encrypted Sessions:** JWTs are symmetrically encrypted with **Fernet** before being injected into `HttpOnly`, `SameSite=Lax` cookies.
- **Data at Rest:** Sensitive columns (URLs, tags) are encrypted using SQLAlchemy `TypeDecorator`.

---

# High-Performance Data Persistence

## Bypassing ORM Bottlenecks

- **FastAPI + SQLModel:** Eliminating dual class definitions; a single class serves as both DB schema and API DTO.
- **asyncpg Engine:** Asynchronous PostgreSQL driver for sub-millisecond query execution.

---

# High-Performance Data Persistence

## Bypassing ORM Bottlenecks

- **Eager Loading:** Rigorous use of `selectinload` to completely eradicate N+1 queries.
- **Absolute Normalization:** Strict junction tables and cascading foreign keys. Orphan records are mathematically impossible.

---

# Infrastructure & Engineering Discipline

## Production-Grade Tooling

- **Deployment:** Containerized via Docker Compose behind a Netbird Reverse Proxy.
- **Schema Management:** Alembic handles all deterministic database migrations.

---

# Infrastructure & Engineering Discipline

## Production-Grade Tooling

- **Strictness:** Ruff and `stylelint` cranked to maximum constraints for zero-defect velocity.
- **Testing:** Playwright E2E visual testing orchestrated with hardware-aware concurrency limits.

---

# Contingency: The Offline Fallback

## Because live demos always break

- **PyInstaller:** The entire application is compiled into a standalone executable.
- **SQLite Fallback:** Automatically detects the offline environment and falls back from PostgreSQL to a local `sqlite:///decimark.db`.
- **In-Memory Cache:** Bypasses Redis seamlessly for local rate-limiting and session management.

---

# Conclusion & Live Demo

**DeciMark** proves that absolute structural discipline—from the frontend CSS Grid to the encrypted PostgreSQL backend—creates a fundamentally superior user experience

*Thank you.*
