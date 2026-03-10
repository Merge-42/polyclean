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


@pytest.fixture
def client_with_cards() -> TestClient:
    """Client pre-populated with 3 cards."""
    storage = FakePokemonStorageWithLifecycle()
    app = create_app(storage)
    client = TestClient(app)

    # Add 3 cards
    for i, name in enumerate(["Charizard", "Blastoise", "Venusaur"]):
        client.post(
            "/cards",
            json={
                "name": name,
                "card_type": "Fire" if i == 0 else "Water" if i == 1 else "Grass",
                "hp": 120 + i * 10,
                "set_name": "Base Set",
                "set_number": i + 1,
                "rarity": "Rare Holo",
                "condition": "mint",
            },
        )
    return client


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_crud_flow(client: TestClient) -> None:
    """Test complete CRUD workflow."""
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
    card_id = add_data["data"]["card_id"]

    # Step 2: Verify card is in list
    list_response = client.get("/cards")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["success"] is True
    assert len(list_data["data"]["cards"]) == 1
    assert list_data["data"]["cards"][0]["name"] == "Charizard"
    assert list_data["data"]["cards"][0]["card_type"] == "Fire"

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
    assert len(list_data_after["data"]["cards"]) == 0


def test_empty_collection_returns_empty_list(client: TestClient) -> None:
    """GET on empty collection returns success with empty cards array."""
    response = client.get("/cards")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["cards"] == []
    assert data["data"]["count"] == 0


def test_multiple_cards_list(client_with_cards: TestClient) -> None:
    """GET returns all cards with correct count."""
    response = client_with_cards.get("/cards")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["cards"]) == 3
    assert data["data"]["count"] == 3


def test_invalid_route_returns_404(client: TestClient) -> None:
    """Invalid route returns 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_get_single_card_not_found(client: TestClient) -> None:
    """GET single card returns 405 if endpoint doesn't exist."""
    # Note: There's no GET /cards/{id} endpoint, so it returns 405
    response = client.get("/cards/99999")
    # 405 = Method Not Allowed (endpoint doesn't exist)
    assert response.status_code == 405


# =============================================================================
# Error Case Tests
# =============================================================================


def test_add_card_invalid_condition(client: TestClient) -> None:
    """Adding card with invalid condition returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            "hp": 120,
            "set_name": "Base Set",
            "set_number": 4,
            "rarity": "Rare Holo",
            "condition": "invalid_condition",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_add_card_negative_hp(client: TestClient) -> None:
    """Adding card with negative HP returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            "hp": -10,
            "set_name": "Base Set",
            "set_number": 4,
            "rarity": "Rare Holo",
            "condition": "mint",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_add_card_empty_name(client: TestClient) -> None:
    """Adding card with empty name returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "",
            "card_type": "Fire",
            "hp": 120,
            "set_name": "Base Set",
            "set_number": 4,
            "rarity": "Rare Holo",
            "condition": "mint",
        },
    )
    assert response.status_code == 422


def test_add_card_missing_required_field(client: TestClient) -> None:
    """Adding card with missing required field returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            # Missing: hp, set_name, set_number, rarity, condition
        },
    )
    assert response.status_code == 422


def test_remove_nonexistent_card(client: TestClient) -> None:
    """Removing non-existent card returns success: false."""
    response = client.delete("/cards/99999")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"] is not None


def test_add_card_hp_exceeds_max(client: TestClient) -> None:
    """Adding card with HP > 1000 returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            "hp": 1001,
            "set_name": "Base Set",
            "set_number": 4,
            "rarity": "Rare Holo",
            "condition": "mint",
        },
    )
    assert response.status_code == 422


def test_add_card_set_number_zero(client: TestClient) -> None:
    """Adding card with set_number < 1 returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            "hp": 120,
            "set_name": "Base Set",
            "set_number": 0,
            "rarity": "Rare Holo",
            "condition": "mint",
        },
    )
    assert response.status_code == 422


def test_add_card_notes_too_long(client: TestClient) -> None:
    """Adding card with notes > 1000 chars returns 422."""
    response = client.post(
        "/cards",
        json={
            "name": "Charizard",
            "card_type": "Fire",
            "hp": 120,
            "set_name": "Base Set",
            "set_number": 4,
            "rarity": "Rare Holo",
            "condition": "mint",
            "notes": "x" * 1001,
        },
    )
    assert response.status_code == 422
