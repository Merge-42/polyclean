from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import aiosqlite
from polyclean.pokemon_card_contract import PokemonCard, PokemonCardStoragePort


class SQLitePokemonAdapter(PokemonCardStoragePort):
    def __init__(self, db_path: str = "pokemon_cards.db") -> None:
        self._db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS pokemon_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                card_type TEXT NOT NULL,
                hp INTEGER NOT NULL,
                set_name TEXT NOT NULL,
                set_number INTEGER NOT NULL,
                rarity TEXT NOT NULL,
                condition TEXT NOT NULL,
                acquired_at TEXT NOT NULL,
                notes TEXT
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
                "SQLitePokemonAdapter not initialized. Call initialize() first."
            )
        return self._conn

    async def save(self, card: PokemonCard) -> PokemonCard:
        conn = self._require_conn()
        cursor = await conn.execute(
            """INSERT INTO pokemon_cards 
               (name, card_type, hp, set_name, set_number, rarity, condition, acquired_at, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card.name,
                card.card_type,
                card.hp,
                card.set_name,
                card.set_number,
                card.rarity,
                card.condition,
                card.acquired_at.isoformat(),
                card.notes,
            ),
        )
        await conn.commit()
        card.id = cursor.lastrowid
        return card

    async def get_by_id(self, card_id: int) -> Optional[PokemonCard]:
        conn = self._require_conn()
        cursor = await conn.execute(
            """SELECT id, name, card_type, hp, set_name, set_number, rarity, condition, acquired_at, notes 
               FROM pokemon_cards WHERE id = ?""",
            (card_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return PokemonCard(
            id=row[0],
            name=row[1],
            card_type=row[2],
            hp=row[3],
            set_name=row[4],
            set_number=row[5],
            rarity=row[6],
            condition=row[7],
            acquired_at=datetime.fromisoformat(row[8]),
            notes=row[9],
        )

    async def get_all(self) -> List[PokemonCard]:
        conn = self._require_conn()
        cursor = await conn.execute(
            """SELECT id, name, card_type, hp, set_name, set_number, rarity, condition, acquired_at, notes 
               FROM pokemon_cards ORDER BY id ASC"""
        )
        rows = await cursor.fetchall()
        return [
            PokemonCard(
                id=r[0],
                name=r[1],
                card_type=r[2],
                hp=r[3],
                set_name=r[4],
                set_number=r[5],
                rarity=r[6],
                condition=r[7],
                acquired_at=datetime.fromisoformat(r[8]),
                notes=r[9],
            )
            for r in rows
        ]

    async def delete(self, card_id: int) -> bool:
        conn = self._require_conn()
        cursor = await conn.execute(
            "DELETE FROM pokemon_cards WHERE id = ?",
            (card_id,),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def update(self, card: PokemonCard) -> PokemonCard:
        if card.id is None:
            raise ValueError("Cannot update card without id")

        conn = self._require_conn()
        await conn.execute(
            """UPDATE pokemon_cards 
               SET name=?, card_type=?, hp=?, set_name=?, set_number=?, rarity=?, condition=?, acquired_at=?, notes=? 
               WHERE id=?""",
            (
                card.name,
                card.card_type,
                card.hp,
                card.set_name,
                card.set_number,
                card.rarity,
                card.condition,
                card.acquired_at.isoformat(),
                card.notes,
                card.id,
            ),
        )
        await conn.commit()
        return card
