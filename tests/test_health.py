"""Basic health check tests."""

import os

from fastapi.testclient import TestClient

# Set required environment variables for testing before importing app
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
os.environ["DATABASE_URL"] = "postgresql+psycopg://test_user:test_pass@localhost:54320/test_db"

from app.main import app  # noqa: E402  # pylint: disable=wrong-import-position

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Hello MemU user!"
