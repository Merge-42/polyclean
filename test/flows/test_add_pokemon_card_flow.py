from test.fakes import FakePokemonStorage

import pytest
from polyclean.add_pokemon_card_flow import AddPokemonCardFlow


@pytest.mark.asyncio
async def test_add_pokemon_card_flow_success(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    flow = AddPokemonCardFlow(fake_pokemon_storage)

    result = await flow.flow(
        name="Charizard",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
    )

    assert result["success"] is True
    assert isinstance(result["card_id"], int)


@pytest.mark.asyncio
async def test_add_pokemon_card_flow_invalid_name(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    flow = AddPokemonCardFlow(fake_pokemon_storage)

    result = await flow.flow(
        name="",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
    )

    assert result["success"] is False
    assert "Invalid input" in result["message"]


@pytest.mark.asyncio
async def test_add_pokemon_card_flow_invalid_condition(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    flow = AddPokemonCardFlow(fake_pokemon_storage)

    result = await flow.flow(
        name="Charizard",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="invalid_condition",
    )

    assert result["success"] is False
    assert "Invalid condition" in result["message"]


@pytest.mark.asyncio
async def test_add_pokemon_card_flow_with_notes(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    flow = AddPokemonCardFlow(fake_pokemon_storage)

    result = await flow.flow(
        name="Pikachu",
        card_type="Electric",
        hp=60,
        set_name="Base Set",
        set_number=58,
        rarity="Common",
        condition="near_mint",
        notes="First edition",
    )

    assert result["success"] is True

    card = await fake_pokemon_storage.get_by_id(result["card_id"])
    assert card is not None
    assert card.notes == "First edition"
