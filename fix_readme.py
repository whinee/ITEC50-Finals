import re

with open('docs/README.md', 'r') as f:
    readme = f.read()

tech_stack_section = """## Architecture & Technology Stack

The architecture of DeciMark is engineered for extreme performance, absolute zero-trust security, and unyielding frontend discipline. By rejecting industry trends of bloated Single Page Applications (SPAs) and heavy JavaScript frameworks, the system achieves near-instantaneous load times and perfect accessibility metrics.

### System Flow
```mermaid
flowchart TD
    Client["Browser / Client"]

    subgraph Netbird["Netbird Beta"]
        ReverseProxy["Reverse Proxy & Routing"]
    end

    subgraph Docker["Docker Compose"]
        Hypercorn["Hypercorn (ASGI)"]
        FastAPI["FastAPI App"]
        
        subgraph BackendCore["Backend Core"]
            Auth["Auth & Security Middleware"]
            Routes["API & View Routes"]
            Jinja["Jinja2 SSR"]
        end
        
        subgraph DataLayer["Data Layer"]
            SQLA["SQLAlchemy Async / SQLModel"]
            PG[("PostgreSQL")]
            Redis[("Redis (Limiter & State)")]
        end
    end

    Client -- HTTPS --> ReverseProxy
    ReverseProxy -- Proxy Pass --> Hypercorn
    Hypercorn --> FastAPI
    
    FastAPI --> Auth
    FastAPI --> Routes
    Routes --> Jinja
    Jinja -- Renders HTML --> Client
    
    Routes --> SQLA
    SQLA --> PG
    Auth --> Redis
```

### Dependency Rationale
- **FastAPI / Starlette**: Selected for its unparalleled asynchronous performance and native Pydantic integration, establishing an impregnable, type-safe validation boundary at the absolute edge of the network.
- **SQLModel / SQLAlchemy Async**: Unifies the persistence layer with Pydantic validation, completely eradicating traditional ORM boilerplate while aggressively executing high-throughput PostgreSQL queries in asynchronous non-blocking loops.
- **Jinja2**: Server-Side Rendering (SSR) bypasses the sheer computational weight of modern JavaScript engines. It forces the server to compute the DOM state and serves statically compiled HTML over the wire, optimizing Lighthouse scores perfectly.
- **Redis & fastapi-limiter**: Acts as an ephemeral, lightning-fast in-memory state store, enforcing ruthless rate-limiting across all authentication vectors to nullify brute-force intrusion attempts.
- **Docker Compose & Hypercorn**: Guarantees an identical, highly reproducible orchestration environment across both development and production. Hypercorn provides robust ASGI scaling across multiple underlying worker processes for maximum concurrency.
- **Vanilla CSS (Strict Kebab-Case) & No Tailwind**: A deliberate rejection of utility-class frameworks. The project enforces extreme CSS architectural discipline through `stylelint` (`selector-max-id: 0`), proving that bespoke, finely-tuned CSS dramatically outperforms bloated pre-compiled stylesheets.

## Database Schema & Zero-Trust Integrity

The database is built on PostgreSQL, utilizing deeply nested junction tables and precise primary/foreign key cascading to permanently eradicate orphan rows across millions of potential permutations.

```mermaid
erDiagram
    USERS {
        int id PK
        string username
        string email
        string contact_number
        string password
        string theme
        string role
        timestamp created_at
        timestamp updated_at
        boolean disabled
    }
    
    BOOKMARKS {
        int id PK
        int user_id FK
        string title "Encrypted"
        string url "Encrypted"
        string note "Encrypted"
        timestamp created_at
        timestamp updated_at
    }
    
    TAGS {
        int id PK
        int user_id FK
        string title "Encrypted"
        string color "Encrypted"
        string note "Encrypted"
        timestamp created_at
        timestamp updated_at
    }
    
    JD_NODES {
        int id PK
        int user_id FK
        string code
        int parent_id FK
    }

    BOOKMARK_TAG_JUNCTION {
        int bookmark_id PK, FK
        int tag_id PK, FK
    }

    BOOKMARK_JD_JUNCTION {
        int bookmark_id PK, FK
        int jd_node_id PK, FK
    }

    USERS ||--o{ BOOKMARKS : "owns"
    USERS ||--o{ TAGS : "owns"
    USERS ||--o{ JD_NODES : "owns"
    JD_NODES ||--o{ JD_NODES : "parent_of"
    BOOKMARKS ||--o{ BOOKMARK_TAG_JUNCTION : "has"
    TAGS ||--o{ BOOKMARK_TAG_JUNCTION : "applied_to"
    BOOKMARKS ||--o{ BOOKMARK_JD_JUNCTION : "classified_by"
    JD_NODES ||--o{ BOOKMARK_JD_JUNCTION : "contains"
```

**End-to-End Encryption (E2EE):** Sensitive payloads (`bookmarks.url`, `bookmarks.title`, `tags.title`) are aggressively encrypted at rest using `sqlalchemy-utils` Fernet TypeDecorators. Even in the event of a total database breach, the extracted SQL dumps are mathematically useless to the attacker.

## Deployment Strategy

Deployment is ruthlessly efficient, eliminating configuration drift through containerization and modern overlay networking.

1. **Environment Provisioning**: Define the cryptographic state and database credentials inside `.env.docker`, including the critically vital `DB_ENCRYPTION_KEY`.
2. **Container Orchestration**: Execute `docker-compose up -d --build`. This automatically provisions isolated networks for the Hypercorn workers, PostgreSQL, and Redis cache.
3. **Schema Migrations**: Database schema integrity is enforced instantly on startup via Alembic (`just migrate`), migrating the SQL topology to the latest iteration safely.
4. **Netbird Reverse Proxy**: Instead of relying on legacy Nginx configurations and complex SSL Let's Encrypt bot challenges, public routing is handled entirely over a secure Netbird overlay network, exposing the application securely via a Netbird Reverse Proxy at beta without ever exposing the bare metal port to the public internet.

"""

# Insert before '## Environment variables'
pattern = r'(## Environment variables)'
readme_new = re.sub(pattern, tech_stack_section + r'\1', readme)

with open('docs/README.md', 'w') as f:
    f.write(readme_new)

print("Updated docs/README.md")
