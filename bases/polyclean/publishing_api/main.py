import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from polyclean.create_post_flow import CreatePostFlow
from polyclean.instagram_contract import InstagramPort
from polyclean.instagram_publish_adapter import InstagramGraphAdapter
from polyclean.posts_contract import PostStoragePort
from polyclean.publish_post_flow import PublishPostFlow
from polyclean.sqlite_post_adapter import SQLitePostAdapter
from pydantic import BaseModel


class CreatePostRequest(BaseModel):
    content: str
    image_url: str


def create_app(storage: PostStoragePort, instagram: InstagramPort) -> FastAPI:
    create_post_flow = CreatePostFlow(storage)
    publish_post_flow = PublishPostFlow(storage, instagram)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Using getattr + None check to support storage implementations
        # with optional lifecycle methods (initialize/close)
        initialize = getattr(storage, "initialize", None)
        if initialize is not None:
            await initialize()
        yield
        close = getattr(storage, "close", None)
        if close is not None:
            await close()

    app = FastAPI(title="PolyClean Publishing API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/posts")
    async def create_post(req: CreatePostRequest) -> dict:
        result = await create_post_flow.flow(
            content=req.content, image_url=req.image_url
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result

    @app.post("/posts/{post_id}/publish")
    async def publish_post(post_id: int) -> dict:
        result = await publish_post_flow.flow(post_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result

    return app


# Dependency injection setup
db_path = os.getenv("DB_PATH", "posts.db")
storage = SQLitePostAdapter(db_path=db_path)

instagram = InstagramGraphAdapter(
    access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
    business_account_id=os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", ""),
)

app = create_app(storage, instagram)
