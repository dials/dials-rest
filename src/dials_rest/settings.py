from pydantic import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str
