# AGENTS.md - PolyClean Development Guide

This document provides essential information for AI agents working on the PolyClean project.

## Project Overview

PolyClean combines python-polylith with Clean Architecture principles. The codebase uses a strict directory structure with `components/` (reusable building blocks), `bases/` (entry points), and `test/` (tests mirror component structure).

## Build, Lint, and Test Commands

### Running Tests

```bash
# Run all tests
uv run pytest -q

# Run a single test file
uv run pytest test/flows/test_create_post_flow.py

# Run a single test by name
uv run pytest test/flows/test_create_post_flow.py::test_create_post_flow_success -v

# Run architecture tests
uv run pytest test/architecture/ -v

# Run with coverage
uv run pytest --cov=polyclean --cov-report=term-missing
```

### Linting & Type Checking

```bash
# Run all linters via trunk (ruff, black, isort, etc.)
trunk check

# Run trunk with auto-fix
trunk check --fix
```

Note: `trunk check` runs ruff, black, isort, and other linters. mypy is disabled in this project.

### Running the Application

```bash
# Start API server with reload
uv run uvicorn polyclean.publishing_api.main:app --reload
```

### Polylith CLI Commands

```bash
uv run poly info
uv run poly deps
uv run poly test diff
```

## Code Style Guidelines

### Import Organization

All Python files must start with:

```python
from __future__ import annotations
```

Imports should be organized in the following order (use `isort` with black profile):

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Good import example
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Protocol

from polyclean.posts_contract import Post, PostStoragePort
```

### Formatting

- Line length: 100 characters maximum
- Use black for formatting (the isort profile is set to "black")
- No trailing whitespace
- Use f-strings for string formatting

### Type Hints

- Always use type hints for function parameters and return types
- Use `Optional[X]` instead of `X | None` for compatibility
- Use `from __future__ import annotations` to enable postponed evaluation

```python
# Good
async def get_by_id(self, post_id: int) -> Optional[Post]: ...

# Good - using Protocol for interfaces
class PostStoragePort(Protocol):
    async def save(self, post: Post) -> Post: ...
    async def get_by_id(self, post_id: int) -> Optional[Post]: ...
```

### Naming Conventions

- Classes: PascalCase (e.g., `CreatePostFlow`, `SQLitePostAdapter`)
- Functions/methods: snake_case (e.g., `get_by_id`, `publish_post`)
- Private methods: prefix with underscore (e.g., `_storage`)
- Constants: SCREAMING_SNAKE_CASE
- Files: snake_case (e.g., `test_create_post_flow.py`)

### Dataclasses for Entities

Use `@dataclass` for simple data containers:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Post:
    id: Optional[int]
    content: str
    image_url: str
    created_at: datetime
    instagram_post_id: Optional[str]
    posted: bool = False

    def mark_as_posted(self, instagram_id: str) -> None:
        self.posted = True
        self.instagram_post_id = instagram_id
```

### Protocols for Ports (Interfaces)

Define interfaces using `Protocol` from `typing`:

```python
from typing import Protocol

class InstagramPort(Protocol):
    async def publish_post(self, image_url: str, caption: str) -> str: ...
    async def validate_connection(self) -> bool: ...
```

### Async/Await

- Use `async`/`await` for I/O-bound operations
- Always mark async test functions with `@pytest.mark.asyncio`
- Use `pytest-asyncio` for async test support

```python
@pytest.mark.asyncio
async def test_create_post_flow_success(fake_post_storage):
    flow = CreatePostFlow(fake_post_storage)
    result = await flow.flow(content="Hello", image_url="https://example.com/img.jpg")
    assert result["success"] is True
```

### Error Handling

- Use exceptions for error conditions
- Return dict with `success` key for flow operations that can fail
- Raise `HTTPException` in FastAPI endpoints for HTTP error responses

```python
# In flows, return error dict
if not content or not image_url:
    return {"success": False, "message": "Invalid input"}

# In API endpoints, raise HTTPException
if not result["success"]:
    raise HTTPException(status_code=400, detail=result["message"])
```

### Dependency Injection

- Pass dependencies through constructor injection
- Use protocols/types for dependency abstraction

```python
class CreatePostFlow:
    def __init__(self, storage: PostStoragePort):
        self._storage = storage
```

## Project Structure

```text
polyclean/
├── components/          # Reusable building blocks
│   └── polyclean/
│       ├── create_post_flow/
│       ├── publish_post_flow/
│       ├── posts_contract/       # Entities and ports
│       ├── instagram_contract/   # Instagram interface
│       ├── sqlite_post_adapter/  # SQLite implementation
│       ├── instagram_publish_adapter/
│       └── rest_adapter_lib/
├── bases/               # Application entry points
│   └── polyclean/
│       └── publishing_api/
├── test/                # Tests mirroring component structure
│   ├── flows/
│   ├── adapters/
│   ├── contracts/
│   ├── architecture/
│   └── fakes/           # Test doubles
└── projects/            # Additional project configs
```

## Architecture Patterns

This project follows Clean Architecture with these layers:

1. **Entities** - Domain objects (in `*_contract` components)
2. **Use Cases** - Business logic (in `*_flow` components)
3. **Ports** - Interface definitions (Protocol classes in `*_contract` components)
4. **Adapters** - External service implementations (in `*_adapter` components)

## Configuration

- Python version: 3.12+
- Dependencies managed with `uv`
- Linting: trunk check (runs ruff, black, isort, etc.)
- Type checking: disabled in this project
- Testing: pytest with pytest-asyncio
