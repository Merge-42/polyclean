import azure.functions as func
from polyclean.pokemon_collection_api.main import app

# Wrap FastAPI app for Azure Functions
app = func.AsgiFunctionApp(app=app, http_auth_level=func.AuthLevel.ANONYMOUS)
