import pytest
from fastapi.testclient import TestClient
from polyclean.posts_contract import Post
from polyclean.publishing_api.main import create_app


class FakePostStorageWithLifecycle:
    def __init__(self) -> None:
        self.posts = {}
        self.next_id = 1

    async def initialize(self) -> None:
        pass

    async def close(self) -> None:
        pass

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


class FakeInstagramPublisher:
    async def validate_connection(self) -> bool:
        return True

    async def publish_post(self, image_url: str, caption: str) -> str:
        return "instagram_12345"


@pytest.fixture
def client() -> TestClient:
    storage = FakePostStorageWithLifecycle()
    instagram = FakeInstagramPublisher()
    app = create_app(storage, instagram)
    return TestClient(app)


def test_create_post_returns_200(client: TestClient) -> None:
    response = client.post(
        "/posts",
        json={"content": "Hello world", "image_url": "https://example.com/img.jpg"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "post_id" in data


def test_create_post_returns_400_on_invalid_input(client: TestClient) -> None:
    response = client.post("/posts", json={"content": "", "image_url": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid input"


def test_publish_post_returns_200_on_success(client: TestClient) -> None:
    create_response = client.post(
        "/posts",
        json={"content": "Hello world", "image_url": "https://example.com/img.jpg"},
    )
    post_id = create_response.json()["post_id"]

    response = client.post(f"/posts/{post_id}/publish")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["instagram_post_id"] == "instagram_12345"


def test_publish_post_returns_400_on_not_found(client: TestClient) -> None:
    response = client.post("/posts/999/publish")
    assert response.status_code == 400
    assert response.json()["detail"] == "Post not found"


def test_publish_post_returns_400_on_already_published(client: TestClient) -> None:
    create_response = client.post(
        "/posts",
        json={"content": "Hello world", "image_url": "https://example.com/img.jpg"},
    )
    post_id = create_response.json()["post_id"]

    client.post(f"/posts/{post_id}/publish")
    response = client.post(f"/posts/{post_id}/publish")

    assert response.status_code == 400
    assert response.json()["detail"] == "Already published"
