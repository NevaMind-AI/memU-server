"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables for all tests."""
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    # Use PostgreSQL from docker-compose for testing
    # Default credentials match docker-compose.yml defaults
    # Note: Port 54320 is the host-mapped port from docker compose
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:54320/memu"
