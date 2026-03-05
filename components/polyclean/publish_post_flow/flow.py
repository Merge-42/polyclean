from __future__ import annotations

from polyclean.instagram_contract import InstagramPort
from polyclean.posts_contract import PostStoragePort


class PublishPostFlow:
    def __init__(self, storage: PostStoragePort, instagram: InstagramPort):
        self._storage = storage
        self._instagram = instagram

    async def flow(self, post_id: int) -> dict:
        post = await self._storage.get_by_id(post_id)
        if not post:
            return {"success": False, "message": "Post not found"}

        if post.posted:
            return {"success": False, "message": "Already published"}

        if not await self._instagram.validate_connection():
            return {"success": False, "message": "Instagram unavailable"}

        instagram_id = await self._instagram.publish_post(
            image_url=post.image_url,
            caption=post.content,
        )

        post.mark_as_posted(instagram_id)
        await self._storage.update(post)

        return {"success": True, "instagram_post_id": instagram_id}
