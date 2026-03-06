class FakeInstagramPublisher:
    def __init__(
        self, connection_valid: bool = True, post_id: str = "instagram_12345"
    ) -> None:
        self._connection_valid = connection_valid
        self._post_id = post_id
        self._should_fail = False

    async def validate_connection(self) -> bool:
        return self._connection_valid

    async def publish_post(self, image_url: str, caption: str) -> str:
        if self._should_fail:
            raise RuntimeError("Instagram API error")
        return self._post_id
