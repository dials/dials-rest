from fastapi import FastAPI

from .routers import find_spots, image
from .settings import Settings

settings = Settings()
app = FastAPI()


app.include_router(find_spots.router)
app.include_router(image.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
