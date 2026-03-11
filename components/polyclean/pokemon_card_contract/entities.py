from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CardCondition(str, Enum):
    MINT = "mint"
    NEAR_MINT = "near_mint"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


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
        try:
            CardCondition(self.condition)
        except ValueError:
            return False
        return True
