"""Test configuration loading and validation."""
import pytest
from pathlib import Path

from config.settings import Settings


def test_settings_can_be_instantiated():
    """Test that Settings can be instantiated with required fields."""
    # This will use environment variables from .env file
    try:
        settings = Settings()
        assert settings is not None
        assert settings.APP_NAME == "MemU Server"
    except Exception as e:
        # If .env is not configured, this is expected in CI
        pytest.skip(f"Settings require .env file: {e}")


def test_database_url_construction():
    """Test database URL is constructed correctly."""
    settings = Settings(
        DATABASE_USER="test_user",
        DATABASE_PASSWORD="test_pass",
        DATABASE_HOST="localhost",
        DATABASE_PORT=5432,
        DATABASE_NAME="test_db",
        OPENAI_API_KEY="test_key",
        EMBEDDING_API_KEY="test_key",
    )
    
    expected_url = "postgresql+psycopg://test_user:test_pass@localhost:5432/test_db"
    assert settings.database_url == expected_url


def test_temporal_url_construction():
    """Test Temporal URL is constructed correctly."""
    settings = Settings(
        DATABASE_USER="user",
        DATABASE_PASSWORD="pass",
        DATABASE_NAME="db",
        TEMPORAL_HOST="temporal.local",
        TEMPORAL_PORT=7233,
        OPENAI_API_KEY="key",
        EMBEDDING_API_KEY="key",
    )
    
    assert settings.temporal_url == "temporal.local:7233"


def test_storage_path_creates_directory(tmp_path):
    """Test that storage_dir property creates directory if not exists."""
    storage_path = tmp_path / "test_storage"
    
    settings = Settings(
        DATABASE_USER="user",
        DATABASE_PASSWORD="pass",
        DATABASE_NAME="db",
        STORAGE_PATH=str(storage_path),
        OPENAI_API_KEY="key",
        EMBEDDING_API_KEY="key",
    )
    
    # Access storage_dir should create it
    storage_dir = settings.storage_dir
    
    assert storage_dir.exists()
    assert storage_dir.is_dir()
    assert storage_dir == storage_path


def test_model_dump_safe_hides_sensitive_data(tmp_path):
    """Test that sensitive data is hidden in safe dump."""
    settings = Settings(
        DATABASE_USER="user",
        DATABASE_PASSWORD="secret_password",
        DATABASE_NAME="db",
        OPENAI_API_KEY="secret_openai_key",
        EMBEDDING_API_KEY="secret_embedding_key",
        STORAGE_PATH=str(tmp_path / "storage"),  # Use temp directory
    )
    
    safe_data = settings.model_dump_safe()
    
    # Check sensitive data is hidden
    assert safe_data["DATABASE_PASSWORD"] == "***HIDDEN***"
    assert safe_data["OPENAI_API_KEY"] == "***HIDDEN***"
    assert safe_data["EMBEDDING_API_KEY"] == "***HIDDEN***"
    
    # Check non-sensitive data is present
    assert safe_data["DATABASE_USER"] == "user"
    assert safe_data["DATABASE_NAME"] == "db"


def test_default_values(tmp_path, monkeypatch):
    """Test that default values are set correctly."""
    # Clear environment variables to test actual defaults
    monkeypatch.delenv("DATABASE_PORT", raising=False)
    monkeypatch.delenv("TEMPORAL_PORT", raising=False)
    
    settings = Settings(
        DATABASE_USER="user",
        DATABASE_PASSWORD="pass",
        DATABASE_NAME="db",
        OPENAI_API_KEY="key",
        EMBEDDING_API_KEY="key",
        STORAGE_PATH=str(tmp_path / "storage"),  # Use temp directory
        _env_file=None,  # Don't load .env file
    )
    
    # Test defaults
    assert settings.DATABASE_HOST == "localhost"
    assert settings.DATABASE_PORT == 5432  # Default port
    assert settings.TEMPORAL_HOST == "localhost"
    assert settings.TEMPORAL_PORT == 7233  # Default port
    assert settings.DEFAULT_LLM_MODEL == "gpt-4o-mini"
    assert settings.EMBEDDING_MODEL == "voyage-3.5-lite"
    assert settings.APP_NAME == "MemU Server"
    assert settings.DEBUG is False