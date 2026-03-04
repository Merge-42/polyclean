# PolyClean (uv + python-polylith) runnable example

This workspace is structured using the **python-polylith** "loose" theme:

- `components/<namespace>/<brick>/...`
- `bases/<namespace>/<base>/...`

Top namespace: `polyclean`

## Install / sync

```bash
uv sync
```

## Run the FastAPI base

```bash
uv run uvicorn polyclean.publishing_api.main:app --reload
```

Notes:
- SQLite defaults to `posts.db` in the repo root (override with `DB_PATH`).
- Instagram adapter uses stub mode unless `INSTAGRAM_REAL_API=true`.

## Smoke test

```bash
uv run pytest -q
```

## Polylith CLI

```bash
uv run poly info
uv run poly deps
uv run poly test diff
```
