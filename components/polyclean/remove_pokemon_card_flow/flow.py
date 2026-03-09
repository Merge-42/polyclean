from __future__ import annotations

from polyclean.pokemon_card_contract import PokemonCardStoragePort


class RemovePokemonCardFlow:
    def __init__(self, storage: PokemonCardStoragePort) -> None:
        self._storage = storage

    async def flow(self, card_id: int) -> dict:
        if card_id is None:
            return {"success": False, "message": "Card ID is required"}

        existing = await self._storage.get_by_id(card_id)
        if not existing:
            return {"success": False, "message": "Card not found"}

        deleted = await self._storage.delete(card_id)
        if deleted:
            return {"success": True, "message": f"Card {card_id} removed"}
        return {"success": False, "message": "Failed to remove card"}
