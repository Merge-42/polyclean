from __future__ import annotations

from datetime import datetime, timezone

from polyclean.posts_contract import Post, PostStoragePort


class CreatePostFlow:
    def __init__(self, storage: PostStoragePort):
        self._storage = storage

    async def flow(self, content: str, image_url: str) -> dict:
        if not content or not image_url:
            return {"success": False, "message": "Invalid input"}

        post = Post(
            id=None,
            content=content,
            image_url=image_url,
            created_at=datetime.now(timezone.utc),
            instagram_post_id=None,
            posted=False,
        )

        saved = await self._storage.save(post)
        return {"success": True, "post_id": saved.id}
