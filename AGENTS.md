# AGENTS.md - PolyClean Development Guide

See [PolyClean.md](./PolyClean.md) for detailed architecture documentation.

## Commands

```bash
# Run all tests
uv run pytest -q

# Run a single test file
uv run pytest test/flows/test_create_post_flow.py

# Run a single test by name
uv run pytest test/flows/test_create_post_flow.py::test_create_post_flow_success -v

# Run with coverage
uv run pytest --cov=polyclean --cov-report=term-missing

# Lint check
trunk check --all
trunk check --fix  # auto-fix

# Separate type check
uv run ty check

# Run API server
uv run uvicorn polyclean.publishing_api.main:app --reload
```

## Polylith Commands

```bash
# Create a new component (brick)
uv run poly create component --name my_feature

# Create a new base
uv run poly create base --name my_api

# Create a new project (deployable service)
uv run poly create project --name my_service

# View workspace info
uv run poly info

# View dependency tree
uv run poly deps

# Run tests for changed bricks only
uv run poly test diff
```

## Project Structure

```text
polyclean/
├── components/          # Reusable building blocks
│   └── polyclean/
│       ├── create_post_flow/
│       ├── publish_post_flow/
│       ├── posts_contract/       # Entities and ports
│       ├── instagram_contract/
│       ├── sqlite_post_adapter/
│       ├── instagram_publish_adapter/
│       └── rest_adapter_lib/
├── bases/               # Entry points
│   └── polyclean/
│       └── publishing_api/
├── projects/            # Deployable services
│   └── publishing_service/
└── test/                # Tests mirror component structure
    ├── flows/
    ├── adapters/
    ├── contracts/
    ├── architecture/
    └── fakes/
```

**Projects** (in `projects/`) are deployable units - each has its own `pyproject.toml` defining which components/bases to include and service-specific dependencies.

## Architecture

All Clean Architecture layers are implemented as Polylith components (bricks) in the `components/` folder:

| Clean Architecture | Polylith Component | Naming Suffix |
| ------------------ | ------------------ | ------------- |
| Entities           | Contract           | `*_contract`  |
| Ports              | Contract           | `*_contract`  |
| Use Cases          | Flow               | `*_flow`      |
| Adapters           | Adapter            | `*_adapter`   |
| Layer Utilities    | Library            | `*_lib`       |

- **Entities** - Domain objects (in `*_contract`)
- **Use Cases** - Business logic (in `*_flow`)
- **Ports** - Interfaces (Protocol classes in `*_contract`)
- **Adapters** - External services (in `*_adapter`)
- **\_lib** - Internal layer utilities (in `*_<layer>_lib`)

## Conventions

- Use `Protocol` for port interfaces
- Flows return `{"success": bool, ...}` dicts
- API endpoints raise `HTTPException` on failure
- Constructor injection for dependencies

## Testing

- Use fakes from `test/fakes/` for test doubles
