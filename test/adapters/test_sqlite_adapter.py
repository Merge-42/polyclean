from datetime import datetime, timezone

import pytest
from polyclean.posts_contract import Post
from polyclean.sqlite_post_adapter import SQLitePostAdapter


@pytest.mark.asyncio
async def test_sqlite_adapter_initialize_and_close(tmp_path):
    db_path = tmp_path / "test_posts.db"
    adapter = SQLitePostAdapter(db_path=str(db_path))

    await adapter.initialize()
    await adapter.close()

    assert db_path.exists()


@pytest.mark.asyncio
async def test_sqlite_adapter_save_and_get_by_id(tmp_path):
    db_path = tmp_path / "test_posts.db"
    adapter = SQLitePostAdapter(db_path=str(db_path))
    await adapter.initialize()

    post = Post(
        id=None,
        content="Test content",
        image_url="https://example.com/img.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id=None,
        posted=False,
    )

    saved = await adapter.save(post)
    assert saved.id is not None

    retrieved = await adapter.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.content == "Test content"
    assert retrieved.image_url == "https://example.com/img.jpg"
    assert retrieved.posted is False

    await adapter.close()


@pytest.mark.asyncio
async def test_sqlite_adapter_update_posted(tmp_path):
    db_path = tmp_path / "test_posts.db"
    adapter = SQLitePostAdapter(db_path=str(db_path))
    await adapter.initialize()

    post = Post(
        id=None,
        content="Test content",
        image_url="https://example.com/img.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id=None,
        posted=False,
    )

    saved = await adapter.save(post)
    assert saved.id is not None
    saved.mark_as_posted("instagram_123")
    await adapter.update(saved)

    retrieved = await adapter.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.posted is True
    assert retrieved.instagram_post_id == "instagram_123"

    await adapter.close()


@pytest.mark.asyncio
async def test_sqlite_adapter_get_unposted(tmp_path):
    db_path = tmp_path / "test_posts.db"
    adapter = SQLitePostAdapter(db_path=str(db_path))
    await adapter.initialize()

    post1 = Post(
        id=None,
        content="Post 1",
        image_url="https://example.com/1.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id=None,
        posted=False,
    )
    post2 = Post(
        id=None,
        content="Post 2",
        image_url="https://example.com/2.jpg",
        created_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id=None,
        posted=True,
    )

    saved1 = await adapter.save(post1)
    await adapter.save(post2)

    unposted = await adapter.get_unposted()
    assert len(unposted) == 1
    assert unposted[0].id == saved1.id

    await adapter.close()


@pytest.mark.asyncio
async def test_sqlite_adapter_no_global_db_file(tmp_path, monkeypatch):

    monkeypatch.chdir(tmp_path)

    adapter = SQLitePostAdapter(db_path="posts.db")
    await adapter.initialize()

    db_files = list(tmp_path.glob("*.db"))
    assert len(db_files) == 1
    assert db_files[0].name == "posts.db"

    await adapter.close()
