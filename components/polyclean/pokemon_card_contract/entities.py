from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PokemonCard:
    id: Optional[int]
    name: str
    card_type: str
    hp: int
    set_name: str
    set_number: int
    rarity: str
    condition: str
    acquired_at: datetime
    notes: Optional[str] = None

    def validate(self) -> bool:
        if not self.name:
            return False
        if self.hp < 0:
            return False
        if self.condition not in [
            "mint",
            "near_mint",
            "excellent",
            "good",
            "fair",
            "poor",
        ]:
            return False
        return True
