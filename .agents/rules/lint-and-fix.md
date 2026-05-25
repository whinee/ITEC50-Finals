---
trigger: always_on
glob:
description:
---

# Code Quality & Linting Rules

## After Every Edits

1. Run `just lint`
2. Fix errors, warnings, and notes
3. Repeat until no errors, warnings, and notes are found

## General Guidelines

All code must adhere to professional software engineering standards, including but not limited to:

- **PEP 8**: Python style guide (88-character line limit)
- **DRY Principle**: Don't repeat yourself
- **KISS Principle**: Keep it simple, stupid

## Security Requirements

### SQL Injection Prevention

- NEVER use f-strings or string concatenation for SQL queries
- ALWAYS use SQLAlchemy parameter binding
- Example: `await session.execute(select(Bookmark).where(Bookmark.id == bookmark_id))`

### XSS Protection

- ALWAYS escape user-generated content
- Use Jinja2 autoescaping (default)
- DO NOT output unescaped user input

### Authentication & Authorization

- All routes must use Dependency Injection for authentication
- Use `get_current_user()` to verify sessions
- Check ownership for all resource modifications
- Return 401/403 for unauthorized access

## Performance Requirements

- Use proper database indexing
- Eager load relationships to avoid N+1 queries
- Cache expensive operations where appropriate
- Use pagination for large datasets

## Code Structure

### File Organization

- API endpoints in `src/api/`
- Models in `src/models/`
- Templates in `src/templates/`
- Scripts in `src/static/scripts/`
- SQL Alchemy: `db/`

### Type Hinting

- All Python functions must have type hints
- Use `Annotated` for dependency injection parameters
    - Example: `user: Annotated[User, Depends(get_current_user)]`

## Documentation

- All code must have docstrings
- Functions: 3-line minimum
- Classes: Description of purpose and usage
- Modules: High-level overview

## Specific Checks

### For Python Files

- [ ] No f-strings in SQL queries
- [ ] Proper use of `async`/`await`
- [ ] Type hints on all parameters and return values
- [ ] Docstrings for all functions and classes
- [ ] Line length <= 120 characters
- [ ] No unused imports
- [ ] Proper error handling
- [ ] Dependency injection used for authentication

### For Jinja2 Templates

- [ ] Autoescaping enabled (default)
- [ ] User input sanitized
- [ ] Proper HTML structure
- [ ] Semantic HTML5 elements
- [ ] Accessibility attributes (ARIA roles where needed)

### For Shell Commands

- [ ] No `sudo` without explicit user approval
- [ ] Use absolute paths for executables
- [ ] Quote all arguments
- [ ] No shell expansion of user input

## Git Commit Requirements

All commits must follow this format:

```
feat: Add bookmark editing functionality

- Implemented backend endpoint for updating bookmarks
- Added frontend edit form
- Included proper authentication checks
- Followed PEP 8 guidelines
```

## Example of Good Code

```python
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from src.db.deps import get_session
from src.models import User
from src.auth import get_current_user

@router.get("/bookmarks/{bookmark_id}")
async def get_bookmark(
    bookmark_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific bookmark by ID"""
    result = await session.execute(
        select(Bookmark)
        .where(Bookmark.id == bookmark_id)
        .where(Bookmark.user_id == user.id)
        .options(selectinload(Bookmark.jd_nodes))
    )
    bookmark = result.scalars().first()
    if not bookmark:
        return JSONResponse(status_code=404, content={"detail": "Bookmark not found"})
    return {"bookmark": bookmark}
```

## Example of Bad Code

```python
@router.get("/bookmarks/{bookmark_id}")
async def get_bookmark(bookmark_id: int, session: AsyncSession = Depends(get_session)):
    # BAD: No authentication
    # BAD: String formatting in SQL
    query = f"SELECT * FROM bookmarks WHERE id = {bookmark_id}"
    result = await session.execute(query)
    return {"bookmark": result.fetchone()}
```

