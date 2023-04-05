from __future__ import annotations

from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str

    @staticmethod
    @lru_cache
    def get():
        return Settings()

    class Config:
        secrets_dir = "/opt/secrets"
