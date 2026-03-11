from polyclean.pokemon_card_contract import PokemonCard


class FakePokemonStorage:
    def __init__(self) -> None:
        self.cards = {}
        self.next_id = 1

    async def save(self, card: PokemonCard) -> PokemonCard:
        card.id = self.next_id
        self.cards[self.next_id] = card
        self.next_id += 1
        return card

    async def get_by_id(self, card_id: int) -> PokemonCard | None:
        return self.cards.get(card_id)

    async def get_all(self) -> list[PokemonCard]:
        return list(self.cards.values())

    async def delete(self, card_id: int) -> bool:
        if card_id in self.cards:
            del self.cards[card_id]
            return True
        return False

    async def update(self, card: PokemonCard) -> PokemonCard:
        self.cards[card.id] = card
        return card
