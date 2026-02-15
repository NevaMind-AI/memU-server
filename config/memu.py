"""MemU configuration for memory service."""

from typing import Any

from pydantic import BaseModel

from config.settings import Settings


class MemUUser(BaseModel):
    """User model for memu-py."""

    user_id: str
    agent_id: str | None = None


def build_memu_llm_profiles(settings: Settings) -> dict[str, Any]:
    """Build LLM profiles for memu-py."""
    return {
        "default": {
            "api_key": settings.OPENAI_API_KEY,
            "base_url": settings.OPENAI_BASE_URL,
            "chat_model": settings.DEFAULT_LLM_MODEL,
        },
        "embedding": {
            "api_key": settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY,
            "base_url": settings.EMBEDDING_BASE_URL,
            "embed_model": settings.EMBEDDING_MODEL,
        },
    }


def build_memu_config(settings: Settings) -> dict[str, Any]:
    """Build memu-py core configuration.

    This configures memu-py to:
    1. Connect to PostgreSQL with pgvector
    2. Auto-create tables (ddl_mode: create)
    3. Use configured LLM profiles
    """
    return {
        "llm_profiles": build_memu_llm_profiles(settings),
        "database_config": {
            "metadata_store": {
                "provider": "postgres",
                "ddl_mode": "create",  # Auto-create tables
                "dsn": settings.DATABASE_URL,
            }
        },
        "user_config": {"model": MemUUser},
    }
