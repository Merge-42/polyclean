import azure.functions as func
from polyclean.pokemon_collection_api.main import create_app, storage

# Create FastAPI app (imported from main.py)
fastapi_app = create_app(storage)


# Azure Functions entry point - wraps FastAPI with ASGI middleware
async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return await func.AsgiMiddleware(fastapi_app).handle(req, context)
