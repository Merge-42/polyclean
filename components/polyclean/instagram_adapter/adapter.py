from __future__ import annotations

import os
import uuid

import httpx

from polyclean.instagram_contract import InstagramPort


class InstagramGraphAdapter(InstagramPort):
    """Instagram implementation.

    Defaults to a stub mode (no real API call) unless INSTAGRAM_REAL_API=true.
    """

    def __init__(self, access_token: str, business_account_id: str):
        self._access_token = access_token
        self._business_account_id = business_account_id
        self._base_url = "https://graph.facebook.com/v18.0"

    async def validate_connection(self) -> bool:
        if os.getenv("INSTAGRAM_REAL_API", "false").lower() != "true":
            return True

        if not self._access_token or not self._business_account_id:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self._base_url}/{self._business_account_id}",
                    params={"access_token": self._access_token},
                )
                return r.status_code == 200
        except Exception:
            return False

    async def publish_post(self, image_url: str, caption: str) -> str:
        if os.getenv("INSTAGRAM_REAL_API", "false").lower() != "true":
            return f"stub_{uuid.uuid4().hex[:12]}"

        if not self._access_token or not self._business_account_id:
            raise RuntimeError("Missing Instagram credentials")

        async with httpx.AsyncClient(timeout=30) as client:
            create_response = await client.post(
                f"{self._base_url}/{self._business_account_id}/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self._access_token,
                },
            )
            create_response.raise_for_status()
            media_id = create_response.json()["id"]

            publish_response = await client.post(
                f"{self._base_url}/{self._business_account_id}/media_publish",
                params={
                    "creation_id": media_id,
                    "access_token": self._access_token,
                },
            )
            publish_response.raise_for_status()
            return publish_response.json()["id"]
