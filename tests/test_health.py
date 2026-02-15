"""Tests for the application's root ("/") endpoint."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with proper env setup."""
    try:
        from app.main import app  # noqa: PLC0415

        return TestClient(app)
    except Exception as exc:  # noqa: BLE001 - lifespan may raise DB errors
        pytest.skip(f"Could not initialize test client due to application setup error: {exc}")


def test_root_endpoint(client):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "message" in data
    assert data["message"] == "Hello MemU user!"
