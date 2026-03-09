import pytest
from fastapi.testclient import TestClient
from polyclean.pokemon_card_contract import PokemonCard
from polyclean.pokemon_collection_api.main import create_app


class FakePokemonStorageWithLifecycle:
    def __init__(self) -> None:
        self.cards = {}
        self.next_id = 1

    async def initialize(self) -> None:
        pass

    async def close(self) -> None:
        pass

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


@pytest.fixture
def client() -> TestClient:
    storage = FakePokemonStorageWithLifecycle()
    app = create_app(storage)
    return TestClient(app)


def test_full_crud_flow(client: TestClient) -> None:
    # Step 1: Add a card
    add_response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            "hp": 120,
            "set_name": "Base Set",
            "set_number": 4,
            "rarity": "Rare Holo",
            "condition": "mint",
        },
    )
    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data["success"] is True
    card_id = add_data["card_id"]

    # Step 2: Verify card is in list
    list_response = client.get("/cards")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["success"] is True
    assert len(list_data["cards"]) == 1
    assert list_data["cards"][0]["name"] == "Charizard"
    assert list_data["cards"][0]["card_type"] == "Fire"

    # Step 3: Remove the card
    delete_response = client.delete(f"/cards/{card_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()
    assert delete_data["success"] is True

    # Step 4: Verify card is gone
    list_response_after = client.get("/cards")
    assert list_response_after.status_code == 200
    list_data_after = list_response_after.json()
    assert list_data_after["success"] is True
    assert len(list_data_after["cards"]) == 0
