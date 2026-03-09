import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from polyclean.add_pokemon_card_flow import AddPokemonCardFlow
from polyclean.list_pokemon_cards_flow import ListPokemonCardsFlow
from polyclean.pokemon_card_contract import PokemonCardStoragePort
from polyclean.remove_pokemon_card_flow import RemovePokemonCardFlow
from polyclean.sqlite_pokemon_adapter import SQLitePokemonAdapter
from pydantic import BaseModel


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

    @app.post("/cards")
    async def add_card(req: AddCardRequest) -> dict:
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
            raise HTTPException(status_code=400, detail=result["message"])
        return result

    @app.get("/cards")
    async def list_cards() -> dict:
        result = await list_cards_flow.flow()
        return result

    @app.delete("/cards/{card_id}")
    async def remove_card(card_id: int) -> dict:
        result = await remove_card_flow.flow(card_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result

    return app


db_path = os.getenv("POKEMON_DB_PATH", "pokemon_cards.db")
storage = SQLitePokemonAdapter(db_path=db_path)

app = create_app(storage)
