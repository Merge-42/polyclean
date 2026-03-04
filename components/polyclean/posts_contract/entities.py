from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Post:
    id: Optional[int]
    content: str
    image_url: str
    created_at: datetime
    instagram_post_id: Optional[str]
    posted: bool = False

    def mark_as_posted(self, instagram_id: str) -> None:
        self.posted = True
        self.instagram_post_id = instagram_id
