from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from polyclean.add_pokemon_card_flow import AddPokemonCardFlow
from polyclean.list_pokemon_cards_flow import ListPokemonCardsFlow
from polyclean.pokemon_card_contract import CardCondition, PokemonCardStoragePort
from polyclean.remove_pokemon_card_flow import RemovePokemonCardFlow
from polyclean.sqlite_pokemon_adapter import SQLitePokemonAdapter
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .logging_ import setup_logging
from .responses import (
    ApiResponse,
    CardCreatedResponse,
    CardListResponse,
    CardRemovedResponse,
    PokemonCardResponse,
)


class AddCardRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Pokemon card name"
    )
    card_type: str = Field(
        ..., min_length=1, description="Card type (e.g., Fire, Water)"
    )
    hp: int = Field(..., ge=0, le=1000, description="Hit points")
    set_name: str = Field(..., min_length=1, description="Set name (e.g., Base Set)")
    set_number: int = Field(..., ge=1, le=1000, description="Card number in set")
    rarity: str = Field(..., min_length=1, description="Rarity (e.g., Rare Holo)")
    condition: CardCondition = Field(..., description="Card condition")
    notes: str | None = Field(
        default=None, max_length=1000, description="Optional notes"
    )

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Name cannot be empty or whitespace")
        # Normalize to title case for consistency
        return v.strip().title()


def create_app(storage: PokemonCardStoragePort) -> FastAPI:
    add_card_flow = AddPokemonCardFlow(storage)
    list_cards_flow = ListPokemonCardsFlow(storage)
    remove_card_flow = RemovePokemonCardFlow(storage)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Configure logging on startup
        log_level = settings.log_level.upper() if settings.log_level else "INFO"
        if settings.db_echo:
            log_level = "DEBUG"
        setup_logging(log_level=log_level, log_file=settings.log_file)
        logger.info(f"Starting {settings.api_title} v{settings.api_version}")

        initialize = getattr(storage, "initialize", None)
        if initialize is not None:
            await initialize()
            logger.info("Database initialized")

        yield

        close = getattr(storage, "close", None)
        if close is not None:
            await close()
            logger.info("Database connection closed")

        logger.info("Application shutdown complete")

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
        logger.debug(f"Adding card: {req.name}")
        result = await add_card_flow.flow(
            name=req.name,
            card_type=req.card_type,
            hp=req.hp,
            set_name=req.set_name,
            set_number=req.set_number,
            rarity=req.rarity,
            condition=req.condition.value,
            notes=req.notes,
        )
        if not result["success"]:
            logger.warning(f"Failed to add card: {result.get('message')}")
            return ApiResponse(
                success=False,
                error=result.get("message", "Failed to add card"),
            )
        logger.info(f"Card added successfully: {req.name} (ID: {result['card_id']})")
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
        logger.debug(f"Removing card ID: {card_id}")
        result = await remove_card_flow.flow(card_id)
        if not result["success"]:
            logger.warning(f"Failed to remove card {card_id}: {result.get('message')}")
            return ApiResponse(
                success=False,
                error=result.get("message", "Card not found"),
            )
        logger.info(f"Card removed successfully: ID {card_id}")
        return ApiResponse(
            success=True,
            data=CardRemovedResponse(removed=True, card_id=card_id),
        )

    return app


storage = SQLitePokemonAdapter(db_path=settings.db_path)

app = create_app(storage)
