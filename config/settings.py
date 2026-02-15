"""Application settings for memu-server."""

from typing import Any

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Values are resolved in order: environment variable > .env file > default.
    """

    # ── Database (docker-compose level) ──
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "memu_dev"

    # ── Database (application level, used by app/database.py) ──
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "memu"
    DATABASE_URL: str = ""

    # ── LLM ──
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"

    # ── Embedding ──
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.voyageai.com/v1"
    EMBEDDING_MODEL: str = "voyage-3.5-lite"

    # ── Temporal ──
    TEMPORAL_HOST: str = "localhost"
    TEMPORAL_PORT: int = 7233
    TEMPORAL_NAMESPACE: str = "default"

    # ── Storage ──
    STORAGE_PATH: str = "./data/storage"

    # ── Computed fields ──
    database_url: str = ""

    @field_validator("database_url", mode="after")
    @classmethod
    def assemble_db_url(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str) and v == "":
            return (
                f"postgresql+psycopg://{info.data['POSTGRES_USER']}:{info.data['POSTGRES_PASSWORD']}"
                f"@{info.data['POSTGRES_HOST']}:{info.data['POSTGRES_PORT']}/{info.data['POSTGRES_DB']}"
            )
        return v

    @property
    def temporal_url(self) -> str:
        return f"{self.TEMPORAL_HOST}:{self.TEMPORAL_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
