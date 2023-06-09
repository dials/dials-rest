from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field

# The pydantic secrets-reading dir, for settings secret settings from file
SECRETS_DIR = Path("/opt/secrets")


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
        if SECRETS_DIR.is_dir():
            secrets_dir = SECRETS_DIR
