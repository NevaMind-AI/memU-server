"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_env(monkeypatch_session):
    """Set up test environment variables for all tests."""
    monkeypatch_session.setenv("OPENAI_API_KEY", "test-key-for-testing")
    monkeypatch_session.setenv("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch fixture."""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()
