from datetime import datetime, timezone

from polyclean.posts_contract import Post


class TestPostEntity:
    def test_mark_as_posted_sets_posted_true(self):
        post = Post(
            id=1,
            content="Test post",
            image_url="https://example.com/img.jpg",
            created_at=datetime.now(timezone.utc),
            instagram_post_id=None,
            posted=False,
        )
        post.mark_as_posted("instagram_12345")

        assert post.posted is True
        assert post.instagram_post_id == "instagram_12345"

    def test_mark_as_posted_overwrites_existing_id(self):
        post = Post(
            id=1,
            content="Test post",
            image_url="https://example.com/img.jpg",
            created_at=datetime.now(timezone.utc),
            instagram_post_id="old_id",
            posted=True,
        )
        post.mark_as_posted("new_id")

        assert post.posted is True
        assert post.instagram_post_id == "new_id"
