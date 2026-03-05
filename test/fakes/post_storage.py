from polyclean.posts_contract import Post


class FakePostStorage:
    def __init__(self):
        self.posts = {}
        self.next_id = 1

    async def save(self, post: Post) -> Post:
        post.id = self.next_id
        self.posts[self.next_id] = post
        self.next_id += 1
        return post

    async def get_by_id(self, post_id: int) -> Post | None:
        return self.posts.get(post_id)

    async def get_unposted(self) -> list[Post]:
        return [p for p in self.posts.values() if not p.posted]

    async def update(self, post: Post) -> Post:
        self.posts[post.id] = post
        return post
