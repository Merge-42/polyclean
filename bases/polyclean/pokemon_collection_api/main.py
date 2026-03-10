import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from polyclean.add_pokemon_card_flow import AddPokemonCardFlow
from polyclean.list_pokemon_cards_flow import ListPokemonCardsFlow
from polyclean.pokemon_card_contract import PokemonCardStoragePort
from polyclean.remove_pokemon_card_flow import RemovePokemonCardFlow
from polyclean.sqlite_pokemon_adapter import SQLitePokemonAdapter
from pydantic import BaseModel

from .responses import (
    ApiResponse,
    CardCreatedResponse,
    CardListResponse,
    CardRemovedResponse,
    PokemonCardResponse,
)


class AddCardRequest(BaseModel):
    name: str
    card_type: str
    hp: int
    set_name: str
    set_number: int
    rarity: str
    condition: str
    notes: str | None = None


def create_app(storage: PokemonCardStoragePort) -> FastAPI:
    add_card_flow = AddPokemonCardFlow(storage)
    list_cards_flow = ListPokemonCardsFlow(storage)
    remove_card_flow = RemovePokemonCardFlow(storage)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        initialize = getattr(storage, "initialize", None)
        if initialize is not None:
            await initialize()
        yield
        close = getattr(storage, "close", None)
        if close is not None:
            await close()

    app = FastAPI(title="Pokemon Collection API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/cards", response_model=ApiResponse[CardCreatedResponse])
    async def add_card(req: AddCardRequest) -> ApiResponse[CardCreatedResponse]:
        result = await add_card_flow.flow(
            name=req.name,
            card_type=req.card_type,
            hp=req.hp,
            set_name=req.set_name,
            set_number=req.set_number,
            rarity=req.rarity,
            condition=req.condition,
            notes=req.notes,
        )
        if not result["success"]:
            return ApiResponse(
                success=False,
                error=result.get("message", "Failed to add card"),
            )
        return ApiResponse(
            success=True,
            data=CardCreatedResponse(card_id=result["card_id"]),
        )

    @app.get("/cards", response_model=ApiResponse[CardListResponse])
    async def list_cards() -> ApiResponse[CardListResponse]:
        result = await list_cards_flow.flow()
        cards = [
            PokemonCardResponse(
                id=card["id"],
                name=card["name"],
                card_type=card["card_type"],
                hp=card["hp"],
                set_name=card["set_name"],
                set_number=card["set_number"],
                rarity=card["rarity"],
                condition=card["condition"],
                acquired_at=card["acquired_at"],
                notes=card.get("notes"),
            )
            for card in result.get("cards", [])
        ]
        return ApiResponse(
            success=True,
            data=CardListResponse(cards=cards, count=len(cards)),
        )

    @app.delete("/cards/{card_id}", response_model=ApiResponse[CardRemovedResponse])
    async def remove_card(card_id: int) -> ApiResponse[CardRemovedResponse]:
        result = await remove_card_flow.flow(card_id)
        if not result["success"]:
            return ApiResponse(
                success=False,
                error=result.get("message", "Card not found"),
            )
        return ApiResponse(
            success=True,
            data=CardRemovedResponse(removed=True, card_id=card_id),
        )

    return app


db_path = os.getenv("POKEMON_DB_PATH", "pokemon_cards.db")
storage = SQLitePokemonAdapter(db_path=db_path)

app = create_app(storage)
