import logging

from fastapi import FastAPI

from .routers import find_spots, image
from .settings import Settings

logging.basicConfig(level=logging.INFO)

settings = Settings()
app = FastAPI()

app.include_router(find_spots.router)
app.include_router(image.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the DIALS REST API!"}
