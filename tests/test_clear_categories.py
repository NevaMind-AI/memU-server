"""Tests for /clear and /categories endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.memory import ClearMemoriesRequest, ListCategoriesRequest


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
            # Temporal connects lazily; pre-set a mock so endpoints don't call real Temporal
            test_client.app.state.temporal = MagicMock()
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


# ── Schema-level input validation tests ──


class TestClearMemoriesRequestValidation:
    """Tests for ClearMemoriesRequest whitespace/blank handling."""

    def test_whitespace_user_id_treated_as_none(self):
        """Blank user_id is stripped to None; agent_id must fill the gap."""
        req = ClearMemoriesRequest(user_id="   ", agent_id="a1")
        assert req.user_id is None
        assert req.agent_id == "a1"

    def test_whitespace_agent_id_treated_as_none(self):
        req = ClearMemoriesRequest(user_id="u1", agent_id="   ")
        assert req.agent_id is None
        assert req.user_id == "u1"

    def test_both_blank_raises(self):
        with pytest.raises(ValidationError, match="At least one"):
            ClearMemoriesRequest(user_id="  ", agent_id="  ")

    def test_empty_string_both_raises(self):
        with pytest.raises(ValidationError, match="At least one"):
            ClearMemoriesRequest(user_id="", agent_id="")

    def test_user_id_stripped(self):
        req = ClearMemoriesRequest(user_id="  u1  ")
        assert req.user_id == "u1"


class TestListCategoriesRequestValidation:
    """Tests for ListCategoriesRequest user_id strip/min_length."""

    def test_empty_user_id_raises(self):
        with pytest.raises(ValidationError, match="user_id"):
            ListCategoriesRequest(user_id="")

    def test_whitespace_user_id_raises(self):
        with pytest.raises(ValidationError, match="user_id"):
            ListCategoriesRequest(user_id="   ")

    def test_user_id_stripped(self):
        req = ListCategoriesRequest(user_id="  u1  ")
        assert req.user_id == "u1"


# ── Endpoint-level validation tests ──


def test_clear_whitespace_user_id_needs_agent(client):
    """POST /clear with blank user_id only → 422 (both effectively None)."""
    response = client.post("/clear", json={"user_id": "   "})
    assert response.status_code == 422


def test_categories_empty_user_id_rejected(client):
    """POST /categories with empty user_id → 422."""
    response = client.post("/categories", json={"user_id": ""})
    assert response.status_code == 422


def test_categories_whitespace_user_id_rejected(client):
    """POST /categories with whitespace-only user_id → 422."""
    response = client.post("/categories", json={"user_id": "   "})
    assert response.status_code == 422


# ── /retrieve query validation tests ──


def test_retrieve_missing_query_rejected(client):
    """POST /retrieve without 'query' key → 400."""
    response = client.post("/retrieve", json={"other": "value"})
    assert response.status_code == 400
    assert "Missing 'query'" in response.json()["detail"]


def test_retrieve_empty_query_rejected(client):
    """POST /retrieve with empty string query → 400."""
    response = client.post("/retrieve", json={"query": ""})
    assert response.status_code == 400
    assert "'query' must be a non-empty string" in response.json()["detail"]


def test_retrieve_whitespace_query_rejected(client):
    """POST /retrieve with whitespace-only query → 400."""
    response = client.post("/retrieve", json={"query": "   "})
    assert response.status_code == 400
    assert "'query' must be a non-empty string" in response.json()["detail"]


def test_retrieve_non_string_query_rejected(client):
    """POST /retrieve with non-string query → 400."""
    response = client.post("/retrieve", json={"query": 123})
    assert response.status_code == 400
    assert "'query' must be a non-empty string" in response.json()["detail"]


def test_retrieve_valid_query_strips_whitespace(mock_service, client):
    """POST /retrieve with valid padded query → stripped value passed to service."""
    mock_service.retrieve = AsyncMock(return_value=[{"memory": "test"}])
    response = client.post("/retrieve", json={"query": "  hello world  "})
    assert response.status_code == 200
    mock_service.retrieve.assert_called_once_with(["hello world"])
