"""Application settings for memu-server."""

from urllib.parse import quote

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Values are resolved in order: environment variable > .env file > default.
    """

    # ── Database ──
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "memu_dev"
    DATABASE_URL: str = ""

    # ── LLM ──
    # Empty defaults: validated at application startup (app/main.py) with a
    # clear RuntimeError.  Keeping defaults allows Settings() to be constructed
    # for config-building and testing without requiring a live API key.
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"

    # ── Embedding ──
    # Falls back to OPENAI_API_KEY in build_memu_llm_profiles when empty
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.voyageai.com/v1"
    EMBEDDING_MODEL: str = "voyage-3.5-lite"

    # ── Temporal ──
    TEMPORAL_HOST: str = "localhost"
    TEMPORAL_PORT: int = 7233
    TEMPORAL_NAMESPACE: str = "default"

    # ── Storage ──
    STORAGE_PATH: str = "./data/storage"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_db_url(cls, v: str, info: ValidationInfo) -> str:
        """Build DATABASE_URL from POSTGRES_* components when not explicitly set."""
        if v.strip():
            return v
        user = quote(info.data["POSTGRES_USER"], safe="")
        password = quote(info.data["POSTGRES_PASSWORD"], safe="")
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{info.data['POSTGRES_HOST']}:{info.data['POSTGRES_PORT']}/{info.data['POSTGRES_DB']}"
        )

    @property
    def temporal_url(self) -> str:
        return f"{self.TEMPORAL_HOST}:{self.TEMPORAL_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
