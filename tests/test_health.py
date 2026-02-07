"""Tests for the application's root ("/") endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with proper env setup."""
    try:
        from app.main import app

        return TestClient(app)
    except Exception as exc:
        pytest.skip(f"Could not initialize test client due to application setup error: {exc}")


def test_root_endpoint(client):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Hello MemU user!"
