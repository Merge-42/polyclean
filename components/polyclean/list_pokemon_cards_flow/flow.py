from __future__ import annotations

from polyclean.pokemon_card_contract import PokemonCardStoragePort


class ListPokemonCardsFlow:
    def __init__(self, storage: PokemonCardStoragePort) -> None:
        self._storage = storage

    async def flow(self) -> dict:
        cards = await self._storage.get_all()
        return {
            "success": True,
            "cards": [
                {
                    "id": card.id,
                    "name": card.name,
                    "card_type": card.card_type,
                    "hp": card.hp,
                    "set_name": card.set_name,
                    "set_number": card.set_number,
                    "rarity": card.rarity,
                    "condition": card.condition,
                    "acquired_at": card.acquired_at.isoformat(),
                    "notes": card.notes,
                }
                for card in cards
            ],
        }
