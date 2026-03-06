from __future__ import annotations

import os
import uuid

from polyclean.instagram_contract import InstagramPort
from polyclean.rest_adapter_lib import build_session


class InstagramGraphAdapter(InstagramPort):
    """Instagram Graph API adapter.

    Uses rest_adapter_lib for a shared session with automatic retry logic.
    Defaults to stub mode unless INSTAGRAM_REAL_API=true.
    """

    def __init__(self, access_token: str, business_account_id: str) -> None:
        self._access_token = access_token
        self._business_account_id = business_account_id
        self._base_url = "https://graph.facebook.com/v18.0"
        self._session = build_session(retries=3)

    async def validate_connection(self) -> bool:
        if os.getenv("INSTAGRAM_REAL_API", "false").lower() != "true":
            return True

        if not self._access_token or not self._business_account_id:
            return False

        try:
            response = self._session.get(
                f"{self._base_url}/{self._business_account_id}",
                params={"access_token": self._access_token},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    async def publish_post(self, image_url: str, caption: str) -> str:
        if os.getenv("INSTAGRAM_REAL_API", "false").lower() != "true":
            return f"stub_{uuid.uuid4().hex[:12]}"

        if not self._access_token or not self._business_account_id:
            raise RuntimeError("Missing Instagram credentials")

        create_response = self._session.post(
            f"{self._base_url}/{self._business_account_id}/media",
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": self._access_token,
            },
            timeout=30,
        )
        create_response.raise_for_status()
        media_id = create_response.json()["id"]

        publish_response = self._session.post(
            f"{self._base_url}/{self._business_account_id}/media_publish",
            params={
                "creation_id": media_id,
                "access_token": self._access_token,
            },
            timeout=30,
        )
        publish_response.raise_for_status()
        return publish_response.json()["id"]
