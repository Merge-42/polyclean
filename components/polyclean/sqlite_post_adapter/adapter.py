from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import aiosqlite
from polyclean.posts_contract import Post, PostStoragePort


class SQLitePostAdapter(PostStoragePort):
    def __init__(self, db_path: str = "posts.db"):
        self._db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                image_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                instagram_post_id TEXT,
                posted INTEGER NOT NULL DEFAULT 0
            )
            """)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    def _require_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError(
                "SQLitePostAdapter not initialized. Call initialize() first."
            )
        return self._conn

    async def save(self, post: Post) -> Post:
        conn = self._require_conn()
        cursor = await conn.execute(
            "INSERT INTO posts (content, image_url, created_at, instagram_post_id, posted) VALUES (?, ?, ?, ?, ?)",
            (
                post.content,
                post.image_url,
                post.created_at.isoformat(),
                post.instagram_post_id,
                int(post.posted),
            ),
        )
        await conn.commit()
        post.id = cursor.lastrowid
        return post

    async def get_by_id(self, post_id: int) -> Optional[Post]:
        conn = self._require_conn()
        cursor = await conn.execute(
            "SELECT id, content, image_url, created_at, instagram_post_id, posted FROM posts WHERE id = ?",
            (post_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Post(
            id=row[0],
            content=row[1],
            image_url=row[2],
            created_at=datetime.fromisoformat(row[3]),
            instagram_post_id=row[4],
            posted=bool(row[5]),
        )

    async def get_unposted(self) -> List[Post]:
        conn = self._require_conn()
        cursor = await conn.execute(
            "SELECT id, content, image_url, created_at, instagram_post_id, posted FROM posts WHERE posted = 0 ORDER BY id ASC"
        )
        rows = await cursor.fetchall()
        return [
            Post(
                id=r[0],
                content=r[1],
                image_url=r[2],
                created_at=datetime.fromisoformat(r[3]),
                instagram_post_id=r[4],
                posted=bool(r[5]),
            )
            for r in rows
        ]

    async def update(self, post: Post) -> Post:
        if post.id is None:
            raise ValueError("Cannot update post without id")

        conn = self._require_conn()
        await conn.execute(
            "UPDATE posts SET content=?, image_url=?, created_at=?, instagram_post_id=?, posted=? WHERE id=?",
            (
                post.content,
                post.image_url,
                post.created_at.isoformat(),
                post.instagram_post_id,
                int(post.posted),
                post.id,
            ),
        )
        await conn.commit()
        return post
