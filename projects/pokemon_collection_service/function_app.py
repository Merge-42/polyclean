import azure.functions as func
from polyclean.pokemon_collection_api.main import app as fastapi_app

# Wrap FastAPI app for Azure Functions
func_app = func.AsgiFunctionApp(
    app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS
)
