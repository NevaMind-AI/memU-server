"""Test environment variable validation."""

import os
import sys

import pytest


def test_app_requires_openai_api_key():
    """Test that app refuses to start when OPENAI_API_KEY is not set."""
    # Save original value
    original_key = os.environ.get("OPENAI_API_KEY")

    try:
        # Remove the environment variable
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        # Remove app.main from sys.modules to force reimport
        if "app.main" in sys.modules:
            del sys.modules["app.main"]

        # Importing app should raise RuntimeError
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY environment variable is not set or is empty"):
            from app.main import app  # noqa: F401

    finally:
        # Restore original value
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        # Clean up module cache
        if "app.main" in sys.modules:
            del sys.modules["app.main"]


def test_app_refuses_empty_openai_api_key():
    """Test that app refuses to start when OPENAI_API_KEY is empty."""
    # Save original value
    original_key = os.environ.get("OPENAI_API_KEY")

    try:
        # Set to empty string
        os.environ["OPENAI_API_KEY"] = ""

        # Remove app.main from sys.modules to force reimport
        if "app.main" in sys.modules:
            del sys.modules["app.main"]

        # Importing app should raise RuntimeError
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY environment variable is not set or is empty"):
            from app.main import app  # noqa: F401

    finally:
        # Restore original value
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
        # Clean up module cache
        if "app.main" in sys.modules:
            del sys.modules["app.main"]


def test_app_starts_with_valid_openai_api_key():
    """Test that app starts successfully with valid OPENAI_API_KEY."""
    # Save original value
    original_key = os.environ.get("OPENAI_API_KEY")

    try:
        # Set valid key
        os.environ["OPENAI_API_KEY"] = "test-valid-key"

        # Remove app.main from sys.modules to force reimport
        if "app.main" in sys.modules:
            del sys.modules["app.main"]

        # Should not raise
        from app.main import app

        assert app is not None
        assert app.title == "memU Server"

    finally:
        # Restore original value
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
        # Clean up module cache
        if "app.main" in sys.modules:
            del sys.modules["app.main"]
