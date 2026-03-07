# PolyClean

A thought experiment combining [python-polylith](https://github.com/DavidVujic/python-polylith) and [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) in Python.

> See [PolyClean.md](./PolyClean.md) for a detailed architectural proposal explaining the layer model, dependency rules, and rationale behind structuring code for human and AI comprehension.

## The Idea

This repository explores whether stricter code organization can help both humans and AI agents manage larger codebases more effectively. By combining:

- **Polylith's** emphasis on small, composable, and reusable building blocks (components and bases)
- **Clean Architecture's** clear separation of concerns (entities, use cases, interfaces, adapters)

We aim to create a structure that encourages writing code in bite-sized, digestible chunks.

## Why It Matters for AI

Large language models excel at generating small, focused pieces of code but struggle with massive files and complex interdependencies. By enforcing:

- Strict directory structure with clear boundaries
- Explicit dependency rules between layers
- Small, single-responsibility components

We can help AI systems produce more maintainable and modular code that humans can actually review and understand.

## Project Structure

```text
polyclean/
├── components/          # Reusable building blocks
│   └── polyclean/
│       ├── create_post_flow/
│       ├── publish_post_flow/
│       ├── posts_contract/
│       ├── instagram_contract/
│       ├── sqlite_post_adapter/
│       └── instagram_publish_adapter/
├── bases/               # Application entry points
│   └── polyclean/
│       └── publishing_api/
├── projects/            # Deployable services
│   └── publishing_service/
└── test/                # Tests mirroring component structure
```

## Setup

Install dependencies:

```bash
uv sync
```

## Run Tests

```bash
uv run pytest -q
```

## Run the API Server

```bash
uv run uvicorn polyclean.publishing_api.main:app --reload
```

The API will start at `http://127.0.0.1:8000`. SQLite database defaults to `posts.db` in the repo root (override with `DB_PATH`).

## Polylith CLI

```bash
uv run poly info
uv run poly deps
uv run poly test diff
```

## Architecture Tests

This repo includes architecture tests that verify:

- Clean Architecture layer dependencies (entities → use cases → interfaces → adapters)
- Polylith component boundaries

Run them with:

```bash
uv run pytest test/architecture/ -v
```
