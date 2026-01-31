"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables for all tests."""
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
