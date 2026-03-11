from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None


class PokemonCardResponse(BaseModel):
    """Single Pokemon card in responses."""

    id: int
    name: str
    card_type: str
    hp: int
    set_name: str
    set_number: int
    rarity: str
    condition: str
    acquired_at: str
    notes: Optional[str] = None


class CardCreatedResponse(BaseModel):
    """Response when a card is created."""

    card_id: int


class CardListResponse(BaseModel):
    """Response containing list of cards."""

    cards: list[PokemonCardResponse]
    count: int


class CardRemovedResponse(BaseModel):
    """Response when a card is removed."""

    removed: bool
    card_id: int
