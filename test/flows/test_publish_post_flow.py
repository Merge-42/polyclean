from datetime import datetime, timezone

import pytest
from polyclean.posts_contract import Post
from polyclean.publish_post_flow import PublishPostFlow


@pytest.mark.asyncio
async def test_publish_post_flow_returns_not_found(
    fake_post_storage, fake_instagram_publisher
):
    flow = PublishPostFlow(fake_post_storage, fake_instagram_publisher)

    result = await flow.flow(post_id=999)

    assert result == {"success": False, "message": "Post not found"}


@pytest.mark.asyncio
async def test_publish_post_flow_returns_already_published(
    fake_post_storage, fake_instagram_publisher
):
    flow = PublishPostFlow(fake_post_storage, fake_instagram_publisher)

    post = Post(
        id=None,
        content="Already posted",
        image_url="https://example.com/img.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id="existing_id",
        posted=True,
    )
    saved = await fake_post_storage.save(post)

    result = await flow.flow(post_id=saved.id)

    assert result == {"success": False, "message": "Already published"}


@pytest.mark.asyncio
async def test_publish_post_flow_returns_instagram_unavailable(
    fake_post_storage, fake_instagram_publisher_unavailable
):
    flow = PublishPostFlow(fake_post_storage, fake_instagram_publisher_unavailable)

    post = Post(
        id=None,
        content="Test post",
        image_url="https://example.com/img.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id=None,
        posted=False,
    )
    saved = await fake_post_storage.save(post)

    result = await flow.flow(post_id=saved.id)

    assert result == {"success": False, "message": "Instagram unavailable"}


@pytest.mark.asyncio
async def test_publish_post_flow_happy_path(
    fake_post_storage, fake_instagram_publisher
):
    flow = PublishPostFlow(fake_post_storage, fake_instagram_publisher)

    post = Post(
        id=None,
        content="Hello world",
        image_url="https://example.com/img.jpg",
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        instagram_post_id=None,
        posted=False,
    )
    saved = await fake_post_storage.save(post)

    result = await flow.flow(post_id=saved.id)

    assert result["success"] is True
    assert result["instagram_post_id"] == "instagram_12345"

    updated_post = await fake_post_storage.get_by_id(saved.id)
    assert updated_post is not None
    assert updated_post.posted is True
    assert updated_post.instagram_post_id == "instagram_12345"
