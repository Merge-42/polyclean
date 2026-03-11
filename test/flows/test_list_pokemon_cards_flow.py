from test.fakes import FakePokemonStorage

import pytest
from polyclean.list_pokemon_cards_flow import ListPokemonCardsFlow
from polyclean.pokemon_card_contract import PokemonCard


@pytest.mark.asyncio
async def test_list_pokemon_cards_flow_empty(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    flow = ListPokemonCardsFlow(fake_pokemon_storage)

    result = await flow.flow()

    assert result["success"] is True
    assert result["cards"] == []


@pytest.mark.asyncio
async def test_list_pokemon_cards_flow_many(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    # Add some cards first
    from datetime import datetime, timezone

    card1 = PokemonCard(
        id=None,
        name="Charizard",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
        acquired_at=datetime.now(timezone.utc),
    )
    card2 = PokemonCard(
        id=None,
        name="Pikachu",
        card_type="Electric",
        hp=60,
        set_name="Base Set",
        set_number=58,
        rarity="Common",
        condition="good",
        acquired_at=datetime.now(timezone.utc),
    )

    await fake_pokemon_storage.save(card1)
    await fake_pokemon_storage.save(card2)

    flow = ListPokemonCardsFlow(fake_pokemon_storage)
    result = await flow.flow()

    assert result["success"] is True
    assert len(result["cards"]) == 2
    assert result["cards"][0]["name"] == "Charizard"
    assert result["cards"][1]["name"] == "Pikachu"


@pytest.mark.asyncio
async def test_list_pokemon_cards_flow_single_card(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    from datetime import datetime, timezone

    card = PokemonCard(
        id=None,
        name="Charizard",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
        acquired_at=datetime.now(timezone.utc),
    )
    await fake_pokemon_storage.save(card)

    flow = ListPokemonCardsFlow(fake_pokemon_storage)
    result = await flow.flow()

    assert result["success"] is True
    assert len(result["cards"]) == 1
    assert result["cards"][0]["name"] == "Charizard"
