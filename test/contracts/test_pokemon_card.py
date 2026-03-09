from datetime import datetime, timezone

from polyclean.pokemon_card_contract import PokemonCard


def test_pokemon_card_validate_valid() -> None:
    card = PokemonCard(
        id=1,
        name="Charizard",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
        acquired_at=datetime.now(timezone.utc),
    )
    assert card.validate() is True


def test_pokemon_card_validate_invalid_name() -> None:
    card = PokemonCard(
        id=1,
        name="",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
        acquired_at=datetime.now(timezone.utc),
    )
    assert card.validate() is False


def test_pokemon_card_validate_invalid_hp() -> None:
    card = PokemonCard(
        id=1,
        name="Charizard",
        card_type="Fire",
        hp=-10,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="mint",
        acquired_at=datetime.now(timezone.utc),
    )
    assert card.validate() is False


def test_pokemon_card_validate_invalid_condition() -> None:
    card = PokemonCard(
        id=1,
        name="Charizard",
        card_type="Fire",
        hp=120,
        set_name="Base Set",
        set_number=4,
        rarity="Rare Holo",
        condition="invalid",
        acquired_at=datetime.now(timezone.utc),
    )
    assert card.validate() is False
