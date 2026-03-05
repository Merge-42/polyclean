import pytest
from polyclean.create_post_flow import CreatePostFlow


@pytest.mark.asyncio
async def test_create_post_flow_returns_failure_on_empty_content(fake_post_storage):
    flow = CreatePostFlow(fake_post_storage)

    result = await flow.flow(content="", image_url="https://example.com/img.jpg")

    assert result == {"success": False, "message": "Invalid input"}


@pytest.mark.asyncio
async def test_create_post_flow_returns_failure_on_empty_image_url(fake_post_storage):
    flow = CreatePostFlow(fake_post_storage)

    result = await flow.flow(content="Hello world", image_url="")

    assert result == {"success": False, "message": "Invalid input"}


@pytest.mark.asyncio
async def test_create_post_flow_returns_failure_on_missing_both(fake_post_storage):
    flow = CreatePostFlow(fake_post_storage)

    result = await flow.flow(content="", image_url="")

    assert result == {"success": False, "message": "Invalid input"}


@pytest.mark.asyncio
async def test_create_post_flow_success(fake_post_storage):
    flow = CreatePostFlow(fake_post_storage)

    result = await flow.flow(
        content="Hello world", image_url="https://example.com/img.jpg"
    )

    assert result["success"] is True
    assert isinstance(result["post_id"], int)

    post = await fake_post_storage.get_by_id(result["post_id"])
    assert post is not None
    assert post.content == "Hello world"
    assert post.image_url == "https://example.com/img.jpg"
    assert post.posted is False
