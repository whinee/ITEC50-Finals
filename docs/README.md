<h1 align="center"><b>
    DeciMark
</b></h1>

<div align="center">
  <br/>
  <strong><em>For Dreanne &mdash;</em></strong><br/>
  <br/>
  <em>who carries ADHD and depression like weather,<br/>
  and forgets some things, as we all do,<br/>
  but has never once let go<br/>
  of the afternoons that made her laugh until it hurt,<br/>
  the moments that made her cry &mdash;<br/>
  out of joy, out of grief, out of being alive &mdash;<br/>
  or any of the small and stubborn evidence<br/>
  that the good times happened.</em><br/>
  <br/>
  <em>For everyone whose brain is a beautiful, exhausting warzone;<br/>
  whose brain loses things without asking.<br/>
  For the ones with the disorders, the diagnoses, the bad weeks<br/>
  swallowed whole by a brain that simply could not keep them.</em><br/>
  <br/>
  For those who have forgotten,<br/>
  but refuse to forget.<br/>
  <br/>
  <em>I have ADHD too. And Bipolar I.<br/>
  My memory is, if anything, worse than hers.<br/>
  I forget more. I lose more.<br/>
  This document exists, in part, because of that.</em><br/>
  <br/>
  I forgot once more<br/>
  Hollow where the knowing was<br/>
  Betrayed by my own<br/>
  <br/>
  <em>This is my pièce de résistance.<br/>
  Not against forgetting &mdash; that fight was already lost<br/>
  the moment I was born with this brain.<br/>
  Against the erasure that follows.<br/>
  A place built to hold what the mind lets go,<br/>
  by someone who knows, firsthand,<br/>
  exactly what it costs to lose it.</em><br/>
  <br/>
</div>

## About DeciMark

DeciMark is a strictly ordered bookmark manager built on the Johnny.Decimal categorization system. It serves as a functional response to the chaos of the human mind, enforcing absolute categorization to transform a sprawling graveyard of forgotten links into a strictly enumerated, reliable directory. It is a system built specifically for those who struggle to remember, providing an external framework that refuses to let information be lost.

Under the hood, it rejects sprawling frameworks and overambitious architectures. It is built cleanly and efficiently using **Python**, **Jinja2**, and foundational **HTML**, **CSS**, and **JS** principles.

For the complete technical breakdown, theoretical justifications, and the engineering philosophy behind this prototype, please read [`paper/main.pdf`](./paper/main.pdf).

## License

See [LICENSE.md](./LICENSE.md) for more details. Please read carefully as the project is dual-licensed. If in doubt, do not hesitate to contact me and inquire about licensing.

## Initial setup

Requires [direnv](https://direnv.net/).

```bash
mkdir -p ~/.config/direnv
# Either copy or append the layout script
cat .direnv.uv >> ~/.config/direnv/direnvrc
direnv allow
```

```sh
pipx install latexminted
```

## What I Had to Run

```sh
uv venv
source .venv
```

```sh
just start-db
```

```sh
just create-db
```

Run the following command if you need to re-initialize `src/migrations`:

```sh
just alembic init src/migrations
```

```sh
just alembic revision --autogenerate -m "init-commit"
```

```sh
just alembic upgrade head
```

## AI Disclosure

In the interest of academic integrity, the following discloses the use of artificial intelligence tools during the development of this project. All architectural decisions, design choices, and implementation strategies were conceived, directed, and validated by the author. AI tools were used as assistive accelerators under the author's explicit instruction and supervision — not as a substitute for understanding.

- **HTML Templates**: The Jinja2 template files under `src/templates/bookmarks` were initially scaffolded with assistance from OpenAI Codex, and subsequently reviewed, corrected, and heavily modified by the author to conform to the application's architecture.
- **Utility Scripts**: Several Python scripts in the `scripts/` directory were drafted with Anthropic's Claude AI as a starting point, with the author directing the logic, reviewing the output, and rewriting where necessary.
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
- **Backend Docstrings**: Google-style docstrings across the backend Python modules were authored with AI assistance to meet documentation standards.
- **Paper Sections**: Certain sections of `paper/main.tex` were drafted collaboratively with AI assistance and then edited by the author, including:
  - The HSL Color Strategy section, the navigation flow TikZ diagram, the Lighthouse Audit appendix, and the Theoretical Foundations chapter.
  - The Abstract, Acknowledgements, and the restructuring of the Dedication into three typographically distinct pages.

The overall system architecture, the Johnny.Decimal integration model, the zero-trust security design, the CSS design system, the JavaScript interaction logic, the database schema, the deployment strategy, and the substantive content of the reflection and rationale were authored entirely by the author. The use of AI tools did not substitute for technical understanding; it accelerated execution of decisions already made.
