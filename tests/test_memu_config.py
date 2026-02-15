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


def test_build_memu_llm_profiles_uses_env_values(monkeypatch):
    """Test that LLM profiles pick up values from environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("DEFAULT_LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("EMBEDDING_API_KEY", "embed-key")

    settings = Settings()
    profiles = build_memu_llm_profiles(settings)

    assert profiles["default"]["api_key"] == "sk-test-key"
    assert profiles["default"]["chat_model"] == "gpt-4o"
    assert profiles["embedding"]["api_key"] == "embed-key"


def test_build_memu_llm_profiles_embedding_fallback():
    """Test that embedding profile falls back to OPENAI_API_KEY when EMBEDDING_API_KEY is empty."""
    settings = Settings(OPENAI_API_KEY="sk-openai", EMBEDDING_API_KEY="")
    profiles = build_memu_llm_profiles(settings)

    assert profiles["embedding"]["api_key"] == "sk-openai"


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


def test_memu_config_database_url_override():
    """Test that an explicit DATABASE_URL overrides POSTGRES_* assembly."""
    explicit_url = "postgresql+psycopg://custom:pass@remote:5432/prod"
    settings = Settings(DATABASE_URL=explicit_url)
    config = build_memu_config(settings)

    dsn = config["database_config"]["metadata_store"]["dsn"]
    assert dsn == explicit_url


def test_memu_config_database_url_password_encoding(monkeypatch):
    """Test that assembled DATABASE_URL properly encodes special characters in password."""
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss:word")
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    # Clear DATABASE_URL so the validator assembles from POSTGRES_* components
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(DATABASE_URL="")
    config = build_memu_config(settings)

    dsn = config["database_config"]["metadata_store"]["dsn"]
    # The raw password with special characters should not appear in the DSN
    assert "p@ss:word" not in dsn
    # URL-encoded representations of '@' and ':' should be present
    assert "%40" in dsn
    assert "%3A" in dsn
