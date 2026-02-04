"""Test environment variable validation using subprocess isolation.

This module uses subprocess isolation to test module-level initialization errors.
This approach avoids issues with shared module state and ensures clean test isolation.
"""

import subprocess
import sys
from pathlib import Path

# Project root directory (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent


def _run_import_test(env_vars: dict[str, str], remove_vars: list[str] | None = None) -> subprocess.CompletedProcess:
    """
    Run a subprocess that attempts to import app.main with specified environment.

    Args:
        env_vars: Environment variables to set
        remove_vars: Environment variables to remove (if any)

    Returns:
        CompletedProcess with returncode, stdout, and stderr
    """
    import os

    # Start with a clean environment based on current env
    env = os.environ.copy()

    # Remove specified variables
    if remove_vars:
        for var in remove_vars:
            env.pop(var, None)

    # Set specified variables
    env.update(env_vars)

    # Run Python subprocess that imports app.main
    result = subprocess.run(
        [sys.executable, "-c", "from app.main import app; print(app.title)"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=30,  # Prevent tests from hanging indefinitely
    )
    return result


def test_app_requires_openai_api_key():
    """Test that app refuses to start when OPENAI_API_KEY is not set."""
    result = _run_import_test(
        env_vars={
            "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/test",
        },
        remove_vars=["OPENAI_API_KEY"],
    )

    assert result.returncode != 0
    assert "OPENAI_API_KEY environment variable is not set or is empty" in result.stderr


def test_app_refuses_empty_openai_api_key():
    """Test that app refuses to start when OPENAI_API_KEY is empty."""
    result = _run_import_test(
        env_vars={
            "OPENAI_API_KEY": "",
            "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/test",
        },
    )

    assert result.returncode != 0
    assert "OPENAI_API_KEY environment variable is not set or is empty" in result.stderr


def test_app_requires_database_url():
    """Test that app refuses to start when DATABASE_URL is not set."""
    result = _run_import_test(
        env_vars={
            "OPENAI_API_KEY": "test-key",
        },
        remove_vars=["DATABASE_URL", "DATABASE_HOST", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_NAME"],
    )

    assert result.returncode != 0
    assert "Database configuration is incomplete" in result.stderr


def test_app_with_individual_db_vars():
    """Test that app starts with individual DATABASE_* variables."""
    result = _run_import_test(
        env_vars={
            "OPENAI_API_KEY": "test-key",
            "DATABASE_HOST": "localhost",
            "DATABASE_PORT": "54320",
            "DATABASE_USER": "test_user",
            "DATABASE_PASSWORD": "test_pass",
            "DATABASE_NAME": "test_db",
        },
        remove_vars=["DATABASE_URL"],
    )

    assert result.returncode == 0
    assert "memU Server" in result.stdout


def test_app_starts_with_valid_openai_api_key():
    """Test that app starts successfully with valid OPENAI_API_KEY."""
    result = _run_import_test(
        env_vars={
            "OPENAI_API_KEY": "test-valid-key",
            "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/test",
        },
    )

    assert result.returncode == 0
    assert "memU Server" in result.stdout
