"""Tests for /clear and /categories endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_service():
    """Create a mock MemoryService."""
    service = MagicMock()
    service.clear_memory = AsyncMock(
        return_value={
            "deleted_categories": ["cat1"],
            "deleted_items": ["item1", "item2"],
            "deleted_resources": [],
        }
    )
    service.list_memory_categories = AsyncMock(
        return_value={
            "categories": [
                {
                    "name": "work",
                    "description": "Work related memories",
                    "user_id": "user123",
                    "agent_id": "agent456",
                    "summary": None,
                }
            ]
        }
    )
    return service


@pytest.fixture
def client(mock_service):
    """Create FastAPI test client with mocked service."""
    from app.main import app

    # Patch create_memory_service so lifespan doesn't connect to a real DB
    with patch("app.main.create_memory_service", return_value=mock_service):
        with TestClient(app) as test_client:
            yield test_client


# ── Clear endpoint tests ──


def test_clear_memory_success(client):
    """Test successful memory clearing."""
    response = client.post("/clear", json={"user_id": "user123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["purged_categories"] == 1
    assert data["result"]["purged_items"] == 2
    assert data["result"]["purged_resources"] == 0


def test_clear_memory_with_agent_id(mock_service, client):
    """Test clearing memory with agent_id."""
    response = client.post("/clear", json={"agent_id": "agent456"})
    assert response.status_code == 200
    mock_service.clear_memory.assert_called_once()


def test_clear_memory_with_both_ids(mock_service, client):
    """Test clearing memory with both user_id and agent_id."""
    response = client.post("/clear", json={"user_id": "user123", "agent_id": "agent456"})
    assert response.status_code == 200
    call_kwargs = mock_service.clear_memory.call_args[1]
    assert call_kwargs["where"] == {"user_id": "user123", "agent_id": "agent456"}


def test_clear_memory_requires_user_or_agent(client):
    """Test that at least one of user_id or agent_id is required."""
    response = client.post("/clear", json={})
    assert response.status_code == 422  # Validation error


def test_clear_memory_service_error(mock_service, client):
    """Test error handling when service fails."""
    mock_service.clear_memory = AsyncMock(side_effect=Exception("Database error"))
    response = client.post("/clear", json={"user_id": "user123"})
    assert response.status_code == 500


# ── Categories endpoint tests ──


def test_list_categories_success(client):
    """Test successful listing of categories."""
    response = client.post("/categories", json={"user_id": "user123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["result"]["categories"]) == 1
    assert data["result"]["categories"][0]["name"] == "work"
    assert data["result"]["categories"][0]["user_id"] == "user123"


def test_list_categories_with_agent_id(mock_service, client):
    """Test listing categories with agent_id filter."""
    response = client.post("/categories", json={"user_id": "user123", "agent_id": "agent456"})
    assert response.status_code == 200
    call_kwargs = mock_service.list_memory_categories.call_args[1]
    assert call_kwargs["where"] == {"user_id": "user123", "agent_id": "agent456"}


def test_list_categories_requires_user_id(client):
    """Test that user_id is required."""
    response = client.post("/categories", json={})
    assert response.status_code == 422  # Validation error


def test_list_categories_empty_result(mock_service, client):
    """Test empty categories response."""
    mock_service.list_memory_categories = AsyncMock(return_value={"categories": []})
    response = client.post("/categories", json={"user_id": "user123"})
    assert response.status_code == 200
    assert response.json()["result"]["categories"] == []


def test_list_categories_service_error(mock_service, client):
    """Test error handling when service fails."""
    mock_service.list_memory_categories = AsyncMock(side_effect=Exception("Database error"))
    response = client.post("/categories", json={"user_id": "user123"})
    assert response.status_code == 500
