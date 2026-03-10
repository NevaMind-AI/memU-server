"""Tests for /memorize and /memorize/status/{task_id} endpoints and related schemas."""

from enum import Enum
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.memory import MemorizeRequest, MemorizeResponse, TaskStatusResponse

# ── Schema unit tests ──


class TestMemorizeRequestSchema:
    """Tests for MemorizeRequest Pydantic model."""

    def test_valid_request_with_dict_conversation(self):
        req = MemorizeRequest(conversation={"role": "user", "content": "hi"}, user_id="u1")
        assert req.user_id == "u1"
        assert req.agent_id == ""
        assert req.override_config is None

    def test_valid_request_with_list_conversation(self):
        req = MemorizeRequest(conversation=[{"role": "user", "content": "hi"}], user_id="u1")
        assert isinstance(req.conversation, list)

    def test_agent_id_default_empty_string(self):
        req = MemorizeRequest(conversation={}, user_id="u1")
        assert req.agent_id == ""

    def test_override_config_accepted(self):
        req = MemorizeRequest(conversation={}, user_id="u1", override_config={"key": "val"})
        assert req.override_config == {"key": "val"}

    def test_missing_conversation_raises(self):
        with pytest.raises(ValidationError, match="conversation"):
            MemorizeRequest(user_id="u1")

    def test_missing_user_id_raises(self):
        with pytest.raises(ValidationError, match="user_id"):
            MemorizeRequest(conversation={})

    def test_empty_user_id_raises(self):
        with pytest.raises(ValidationError, match="user_id"):
            MemorizeRequest(conversation={}, user_id="")

    def test_whitespace_user_id_raises(self):
        with pytest.raises(ValidationError, match="user_id"):
            MemorizeRequest(conversation={}, user_id="   ")

    def test_user_id_stripped(self):
        req = MemorizeRequest(conversation={}, user_id="  u1  ")
        assert req.user_id == "u1"


class TestMemorizeResponseSchema:
    """Tests for MemorizeResponse Pydantic model."""

    def test_defaults(self):
        resp = MemorizeResponse(task_id="wf-123")
        assert resp.status == "PENDING"
        assert resp.message == "Memorization task submitted"

    def test_custom_values(self):
        resp = MemorizeResponse(task_id="wf-1", status="RUNNING", message="custom")
        assert resp.status == "RUNNING"
        assert resp.message == "custom"


class TestTaskStatusResponseSchema:
    """Tests for TaskStatusResponse Pydantic model."""

    def test_defaults(self):
        resp = TaskStatusResponse(task_id="wf-1", status="RUNNING")
        assert resp.detail is None

    def test_with_detail(self):
        resp = TaskStatusResponse(task_id="wf-1", status="FAILED", detail="timeout")
        assert resp.detail == "timeout"


# ── Endpoint tests ──


# Helpers to simulate Temporal workflow status enum values
class _FakeStatus(Enum):
    RUNNING = 1
    COMPLETED = 2
    FAILED = 3


def _make_workflow_description(status_name: str):
    """Build a fake describe() result with a .status.name attribute."""
    desc = MagicMock()
    desc.status = getattr(_FakeStatus, status_name)
    return desc


@pytest.fixture
def mock_temporal():
    """Create a mock Temporal client for endpoint tests."""
    temporal = MagicMock()
    temporal.start_workflow = AsyncMock(return_value=None)
    return temporal


@pytest.fixture
def mock_service():
    """Create a mock MemoryService (needed by lifespan)."""
    return MagicMock()


@pytest.fixture
def client(mock_service, mock_temporal, tmp_path):
    """Create FastAPI test client with mocked service and Temporal."""
    from app.main import app

    with (
        patch("app.main.create_memory_service", return_value=mock_service),
        patch("app.main.storage_dir", tmp_path),
    ):
        with TestClient(app) as test_client:
            # Pre-set mock Temporal client so lazy connect is bypassed
            test_client.app.state.temporal = mock_temporal
            yield test_client


# ── POST /memorize ──


def test_memorize_success(client, mock_temporal):
    """Test successful memorize submission returns PENDING status."""
    response = client.post(
        "/memorize",
        json={"conversation": {"role": "user"}, "user_id": "u1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    result = data["result"]
    assert result["status"] == "PENDING"
    assert result["task_id"].startswith("memorize-")
    assert "u1" in result["message"]
    mock_temporal.start_workflow.assert_called_once()


def test_memorize_with_agent_id(client, mock_temporal):
    """Test memorize includes agent_id in workflow spec."""
    response = client.post(
        "/memorize",
        json={"conversation": {}, "user_id": "u1", "agent_id": "a1"},
    )
    assert response.status_code == 200
    # Verify the spec passed to start_workflow contains agent_id
    call_args = mock_temporal.start_workflow.call_args
    spec = call_args.args[1]
    assert spec["agent_id"] == "a1"


def test_memorize_resource_url_is_filename(client, mock_temporal):
    """Test that resource_url in spec is a filename, not an absolute path."""
    client.post(
        "/memorize",
        json={"conversation": {}, "user_id": "u1"},
    )
    spec = mock_temporal.start_workflow.call_args.args[1]
    resource_url = spec["resource_url"]
    assert resource_url.startswith("conversation-")
    assert "/" not in resource_url


def test_memorize_with_override_config(client, mock_temporal):
    """Test memorize passes override_config in workflow spec."""
    response = client.post(
        "/memorize",
        json={"conversation": {}, "user_id": "u1", "override_config": {"k": "v"}},
    )
    assert response.status_code == 200
    spec = mock_temporal.start_workflow.call_args.args[1]
    assert spec["override_config"] == {"k": "v"}


def test_memorize_saves_conversation_file(client, tmp_path):
    """Test that /memorize saves conversation to a JSON file."""
    response = client.post(
        "/memorize",
        json={"conversation": {"msg": "hello"}, "user_id": "u1"},
    )
    assert response.status_code == 200
    # A conversation file should have been created under the patched storage_dir
    files = list(tmp_path.glob("conversation-*.json"))
    assert len(files) == 1


def test_memorize_missing_user_id(client):
    """Test that missing user_id returns 422."""
    response = client.post("/memorize", json={"conversation": {}})
    assert response.status_code == 422


def test_memorize_missing_conversation(client):
    """Test that missing conversation returns 422."""
    response = client.post("/memorize", json={"user_id": "u1"})
    assert response.status_code == 422


def test_memorize_temporal_error(client, mock_temporal, tmp_path):
    """Test that Temporal failure returns 500 and cleans up orphaned file."""
    mock_temporal.start_workflow = AsyncMock(side_effect=Exception("connection refused"))
    response = client.post(
        "/memorize",
        json={"conversation": {}, "user_id": "u1"},
    )
    assert response.status_code == 500
    assert "Failed to submit" in response.json()["detail"]
    # Orphaned conversation file should be cleaned up
    files = list(tmp_path.glob("conversation-*.json"))
    assert len(files) == 0


def test_memorize_uses_correct_task_queue(client, mock_temporal):
    """Test that workflow is started on the memu-worker task queue."""
    from app.workers.worker import TASK_QUEUE

    client.post("/memorize", json={"conversation": {}, "user_id": "u1"})
    call_kwargs = mock_temporal.start_workflow.call_args.kwargs
    assert call_kwargs["task_queue"] == TASK_QUEUE


def test_memorize_workflow_id_format(client, mock_temporal):
    """Test workflow_id is 'memorize-<hex>'."""
    response = client.post(
        "/memorize",
        json={"conversation": {}, "user_id": "u1"},
    )
    task_id = response.json()["result"]["task_id"]
    assert task_id.startswith("memorize-")
    # The hex portion should be exactly 32 chars (uuid4 hex)
    hex_part = task_id.removeprefix("memorize-")
    assert len(hex_part) == 32


# ── GET /memorize/status/{task_id} ──


def test_status_running(client, mock_temporal):
    """Test status endpoint returns RUNNING for an active workflow."""
    handle = MagicMock()
    handle.describe = AsyncMock(return_value=_make_workflow_description("RUNNING"))
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    result = data["result"]
    assert result["task_id"] == "memorize-abc123"
    assert result["status"] == "RUNNING"
    assert result["detail"] is None


def test_status_completed(client, mock_temporal):
    """Test status endpoint returns COMPLETED with detail."""
    handle = MagicMock()
    handle.describe = AsyncMock(return_value=_make_workflow_description("COMPLETED"))
    handle.result = AsyncMock(return_value={"status": "SUCCESS", "finished_at": "2025-03-06T00:00:00"})
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "COMPLETED"
    assert result["detail"] == "SUCCESS"


def test_status_failed(client, mock_temporal):
    """Test status endpoint returns FAILED with detail message."""
    handle = MagicMock()
    handle.describe = AsyncMock(return_value=_make_workflow_description("FAILED"))
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "FAILED"
    assert result["detail"] == "Task execution failed"


def test_status_not_found(client, mock_temporal):
    """Test 404 when workflow does not exist (RPCError NOT_FOUND)."""
    from temporalio.service import RPCError, RPCStatusCode

    handle = MagicMock()
    handle.describe = AsyncMock(
        side_effect=RPCError("workflow not found", RPCStatusCode.NOT_FOUND, b""),
    )
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_status_rpc_error_returns_500(client, mock_temporal):
    """Test that non-NOT_FOUND RPCError returns 500."""
    from temporalio.service import RPCError, RPCStatusCode

    handle = MagicMock()
    handle.describe = AsyncMock(
        side_effect=RPCError("unavailable", RPCStatusCode.UNAVAILABLE, b""),
    )
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_status_unexpected_error_returns_500(client, mock_temporal):
    """Test that unexpected exceptions return 500."""
    handle = MagicMock()
    handle.describe = AsyncMock(side_effect=RuntimeError("unexpected"))
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_status_unknown_when_status_is_none(client, mock_temporal):
    """Test UNKNOWN is returned when describe().status is None."""
    handle = MagicMock()
    desc = MagicMock()
    desc.status = None
    handle.describe = AsyncMock(return_value=desc)
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "UNKNOWN"
    assert result["detail"] is None


def test_status_completed_missing_status_key(client, mock_temporal):
    """Test COMPLETED workflow where result dict lacks 'status' key falls back to 'SUCCESS'."""
    handle = MagicMock()
    handle.describe = AsyncMock(return_value=_make_workflow_description("COMPLETED"))
    handle.result = AsyncMock(return_value={"task_id": "t1"})
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    result = response.json()["result"]
    assert result["status"] == "COMPLETED"
    assert result["detail"] == "SUCCESS"


def test_status_completed_non_dict_result(client, mock_temporal):
    """Test COMPLETED workflow with a non-dict result (e.g. string) uses str()."""
    handle = MagicMock()
    handle.describe = AsyncMock(return_value=_make_workflow_description("COMPLETED"))
    handle.result = AsyncMock(return_value="some-string-result")
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    result = response.json()["result"]
    assert result["status"] == "COMPLETED"
    assert result["detail"] == "some-string-result"


def test_status_completed_none_result(client, mock_temporal):
    """Test COMPLETED workflow with None result defaults detail to 'SUCCESS'."""
    handle = MagicMock()
    handle.describe = AsyncMock(return_value=_make_workflow_description("COMPLETED"))
    handle.result = AsyncMock(return_value=None)
    mock_temporal.get_workflow_handle = MagicMock(return_value=handle)

    response = client.get("/memorize/status/memorize-abc123")
    result = response.json()["result"]
    assert result["status"] == "COMPLETED"
    assert result["detail"] == "SUCCESS"
