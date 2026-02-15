"""Tests for memu configuration."""

from config.memu import MemUUser, build_memu_config, build_memu_llm_profiles
from config.settings import Settings


def test_memu_user_model():
    """Test MemUUser model."""
    user = MemUUser(user_id="user123", agent_id="agent456")
    assert user.user_id == "user123"
    assert user.agent_id == "agent456"


def test_memu_user_optional_agent():
    """Test MemUUser with optional agent_id."""
    user = MemUUser(user_id="user123")
    assert user.user_id == "user123"
    assert user.agent_id is None


def test_build_memu_llm_profiles():
    """Test building LLM profiles."""
    settings = Settings()
    profiles = build_memu_llm_profiles(settings)

    assert "default" in profiles
    assert "embedding" in profiles
    assert "api_key" in profiles["default"]
    assert "chat_model" in profiles["default"]
    assert "embed_model" in profiles["embedding"]


def test_build_memu_config():
    """Test building complete memu config."""
    settings = Settings()
    config = build_memu_config(settings)

    assert "llm_profiles" in config
    assert "database_config" in config
    assert "user_config" in config

    # Check database config
    db_config = config["database_config"]["metadata_store"]
    assert db_config["provider"] == "postgres"
    assert db_config["ddl_mode"] == "create"
    assert db_config["dsn"] is not None

    # Check user config
    assert config["user_config"]["model"] == MemUUser


def test_memu_config_database_url():
    """Test that memu config uses correct database URL."""
    settings = Settings()
    config = build_memu_config(settings)

    dsn = config["database_config"]["metadata_store"]["dsn"]
    assert "postgresql+psycopg" in dsn
    assert settings.POSTGRES_DB in dsn
