from pathlib import Path

import pytest
from polyclean.create_post_flow import CreatePostFlow
from polyclean.sqlite_post_adapter import SQLitePostAdapter


@pytest.mark.asyncio
async def test_create_post_flow_smoke(tmp_path: Path) -> None:
    db_path = tmp_path / "posts.db"
    storage = SQLitePostAdapter(db_path=str(db_path))
    await storage.initialize()

    flow = CreatePostFlow(storage)
    res = await flow.flow("hi", "https://example.com/x.jpg")
    assert res["success"] is True
    assert isinstance(res["post_id"], int)

    await storage.close()
