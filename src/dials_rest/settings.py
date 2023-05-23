from __future__ import annotations

from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    jwt_secret: str
    enable_metrics: bool = Field(
        default=False,
        description="Expose metrics in prometheus format on the /metrics endpoint",
    )

    @staticmethod
    @lru_cache
    def get():
        return Settings()

    class Config:
        env_prefix = "DIALS_REST_"
        secrets_dir = "/opt/secrets"
