from fastapi import FastAPI

from .routers import image

app = FastAPI()


app.include_router(image.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
