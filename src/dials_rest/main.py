import logging

from fastapi import FastAPI

from .routers import find_spots, image
from .settings import Settings

logging.basicConfig(level=logging.INFO)

settings = Settings()
app = FastAPI()

app.include_router(find_spots.router)
app.include_router(image.router)

if settings.enable_metrics:
    from prometheus_fastapi_instrumentator import Instrumentator

    instrumentator = Instrumentator(
        excluded_handlers=["/metrics"],
    )
    instrumentator.instrument(app)
    instrumentator.expose(app)


@app.get("/")
async def root():
    return {"message": "Welcome to the DIALS REST API!"}
