from test.fakes import FakePokemonStorage

import pytest
from polyclean.pokemon_card_contract import PokemonCard
from polyclean.remove_pokemon_card_flow import RemovePokemonCardFlow


@pytest.mark.asyncio
async def test_remove_pokemon_card_flow_success(
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
    saved = await fake_pokemon_storage.save(card)
    assert saved.id is not None

    flow = RemovePokemonCardFlow(fake_pokemon_storage)
    result = await flow.flow(saved.id)

    assert result["success"] is True
    assert "removed" in result["message"]

    # Verify card is deleted
    deleted = await fake_pokemon_storage.get_by_id(saved.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_remove_pokemon_card_flow_not_found(
    fake_pokemon_storage: FakePokemonStorage,
) -> None:
    flow = RemovePokemonCardFlow(fake_pokemon_storage)
    result = await flow.flow(999)

    assert result["success"] is False
    assert "not found" in result["message"]
