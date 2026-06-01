# Script

## Slide 1: Intro

Good morning, panelists. My name is a.k.a Lyra. While this assignment was meant for groups of four, I am presenting DeciMark as an individual submission. It is a zero-trust, server-backed bookmark manager built to strictly fulfill the 'Full-Stack Concepts' MVP requirement, while significantly expanding upon modern engineering standards.

## Slide 2: Research & Requirements (Phase 1)

For my research, I evaluated Pinboard and Raindrop.io. Pinboard uses flat tags and lacks visual clarity, while Raindrop uses deep folders that inevitably bury information. DeciMark solves this by natively enforcing the Johnny.Decimal system. Every bookmark requires a two-part numeric identifier—Area, Category, and ID. It is structurally deterministic.

## Slide 3: Design & The Cascade (Phase 2)

Per the rubric, the layout uses CSS Grid and Flexbox. But rather than using fragile media queries, I used CSS Grid with an algorithmic `repeat(auto-fill, minmax(280px, 1fr))` definition. The browser dynamically computes the columns. I also globally applied `box-sizing: border-box` to ensure padding is absorbed inward, protecting my flexbox alignments.

## Slide 4: Specificity & Inheritance (Phase 2)

To demonstrate mastery of the Cascade, I managed CSS specificity through a strictly flat hierarchy. The biggest conflict was overriding icon colors based on context. I created a base `.svg-icon` class with low specificity, and then used a contextual selector—`.bookmark-card .icon-delete`—to safely change the `background-color` without ever needing to use the `!important` flag.

## Slide 5: Media Optimization & Typography (Phase 3)

For media optimization, I completely banned raster images. Every icon is an SVG rendered through the CSS `mask-image` property. I also implemented a global HSL color strategy. To switch from light to dark mode, I only shift the Lightness variable, keeping the Hue perfectly mathematically aligned. Furthermore, to guarantee zero-trust privacy, I bypassed Google Fonts entirely, building a custom Python script to compile TrueType fonts into ultra-compressed local WOFF2 binaries.

## Slide 6: System Logic (Phase 4)

For JavaScript logic, the client-side state is a module-scoped Array of Bookmark objects. When filtering tags, I use conditional logic via `Array.prototype.filter()` which feeds into a `for...of` render loop. Crucially, for DOM output, I strictly use `document.createElement()` rather than string templates to completely mitigate Cross-Site Scripting vulnerabilities.

## Slide 7: Reflection

Reflecting on the Client-Server model: it taught me that a frontend click is not reality; the database is reality. I built a Pessimistic UI. When you delete a bookmark, it stays on screen until the backend explicitly returns a 204 No Content response. As for the Cascade, I solved the dark mode UI flash by having Jinja2 inject the theme attribute directly into the HTML element before the first paint.

## Slide 8: Backend Architecture

Now, we're gonna move beyond the rubric―into Enterprise Engineering!

## Slide 9: Zero-Trust Cryptography

While the frontend fulfills the rubric, the backend operates on an enterprise-grade zero-trust architecture. Passwords are not just hashed; they are processed through Argon2id. When authenticated, the server mints a JWT, symmetrically encrypts it with Fernet, and locks it inside an `HttpOnly`, `SameSite=Lax` cookie. Even the database URLs are encrypted at rest using a SQLAlchemy `TypeDecorator`.

## Slide 10: High-Performance Data Persistence (Part 1)

Moving into the persistence layer, I wanted to completely bypass traditional ORM bottlenecks. In standard architectures, developers often write two separate class definitions for the same entity: one for the database schema and one for the API Data Transfer Object. I eliminated this duplication by combining FastAPI with SQLModel. In DeciMark, a single class securely serves as both the database model and the API validation schema. To power this, I utilized the asyncpg driver—the fastest asynchronous PostgreSQL driver for Python—which allows the system to execute complex, multi-table JOIN queries with near-zero latency.

## Slide 11: High-Performance Data Persistence (Part 2)

But a fast driver isn't enough if the queries themselves are inefficient. I aggressively eradicated the dreaded N+1 query problem through the rigorous use of SQLAlchemy's selectinload eager loading strategies. Furthermore, the database schema topology enforces absolute normalization. The complex many-to-many relationships—like linking bookmarks to tags and Johnny.Decimal nodes—are managed through highly optimized junction tables. By enforcing strict unique constraints and cascading foreign keys, the database mechanically guarantees that orphan records are instantly annihilated upon parent deletion. Orphan records are mathematically impossible in this system.

## Slide 12: Infrastructure & Engineering Discipline

The system is deployed via Docker Compose behind a Netbird Reverse Proxy. Database changes are handled deterministically through Alembic migrations. The entire codebase enforces maximum strictness using Ruff and Stylelint, and is verified by a hardware-aware Playwright end-to-end visual testing suite.

## Slide 13: Contingency: The Offline Fallback

Finally, because live demos rely on unpredictable networks, I engineered a contingency. The entire application can run as a PyInstaller standalone executable. If it detects it's running offline, it seamlessly falls back from PostgreSQL and Redis to a local SQLite database and in-memory cache.

## Slide 14: Conclusion

DeciMark proves that absolute structural discipline creates better software. Thank you. I will now start the live demo.
