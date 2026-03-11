from __future__ import annotations

from datetime import datetime, timezone

from polyclean.pokemon_card_contract import (
    CardCondition,
    PokemonCard,
    PokemonCardStoragePort,
)


class AddPokemonCardFlow:
    def __init__(self, storage: PokemonCardStoragePort) -> None:
        self._storage = storage

    async def flow(
        self,
        name: str,
        card_type: str,
        hp: int,
        set_name: str,
        set_number: int,
        rarity: str,
        condition: str,
        notes: str | None = None,
    ) -> dict:
        if not name or not card_type or hp < 0:
            return {"success": False, "message": "Invalid input"}

        valid_conditions = [c.value for c in CardCondition]
        try:
            CardCondition(condition)
        except ValueError:
            return {
                "success": False,
                "message": f"Invalid condition. Must be one of: {valid_conditions}",
            }

        card = PokemonCard(
            id=None,
            name=name,
            card_type=card_type,
            hp=hp,
            set_name=set_name,
            set_number=set_number,
            rarity=rarity,
            condition=condition,
            acquired_at=datetime.now(timezone.utc),
            notes=notes,
        )

        if not card.validate():
            return {"success": False, "message": "Card validation failed"}

        saved = await self._storage.save(card)
        return {"success": True, "card_id": saved.id}
