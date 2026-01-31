"""Test environment variable validation."""

import sys

import pytest


def test_app_requires_openai_api_key(monkeypatch):
    """Test that app refuses to start when OPENAI_API_KEY is not set."""
    # Remove the environment variable
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Remove app.main from sys.modules to force reimport
    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    # Importing app should raise RuntimeError
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY environment variable is not set or is empty"):
        from app.main import app  # noqa: F401

    # Clean up
    if "app.main" in sys.modules:
        del sys.modules["app.main"]


def test_app_refuses_empty_openai_api_key(monkeypatch):
    """Test that app refuses to start when OPENAI_API_KEY is empty."""
    # Set to empty string
    monkeypatch.setenv("OPENAI_API_KEY", "")

    # Remove app.main from sys.modules to force reimport
    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    # Importing app should raise RuntimeError
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY environment variable is not set or is empty"):
        from app.main import app  # noqa: F401

    # Clean up
    if "app.main" in sys.modules:
        del sys.modules["app.main"]


def test_app_requires_database_url(monkeypatch):
    """Test that app refuses to start when DATABASE_URL is not set."""
    # Set valid API key but no DATABASE_URL
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Also remove individual DB vars
    for var in ["DATABASE_HOST", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_NAME"]:
        monkeypatch.delenv(var, raising=False)

    # Remove app.main from sys.modules to force reimport
    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    # Importing app should raise RuntimeError
    with pytest.raises(RuntimeError, match="Database configuration is not set correctly"):
        from app.main import app  # noqa: F401

    # Clean up
    if "app.main" in sys.modules:
        del sys.modules["app.main"]


def test_app_with_individual_db_vars(monkeypatch):
    """Test that app starts with individual DATABASE_* variables."""
    # Set valid API key and individual DB variables
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_HOST", "localhost")
    monkeypatch.setenv("DATABASE_PORT", "54320")
    monkeypatch.setenv("DATABASE_USER", "test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "test_pass")
    monkeypatch.setenv("DATABASE_NAME", "test_db")

    # Remove app.main from sys.modules to force reimport
    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    # Should not raise
    from app.main import app

    assert app is not None
    assert app.title == "memU Server"

    # Clean up
    if "app.main" in sys.modules:
        del sys.modules["app.main"]


def test_app_starts_with_valid_openai_api_key(monkeypatch):
    """Test that app starts successfully with valid OPENAI_API_KEY."""
    # Set valid key and database URL
    monkeypatch.setenv("OPENAI_API_KEY", "test-valid-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")

    # Remove app.main from sys.modules to force reimport
    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    # Should not raise
    from app.main import app

    assert app is not None
    assert app.title == "memU Server"

    # Clean up
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
