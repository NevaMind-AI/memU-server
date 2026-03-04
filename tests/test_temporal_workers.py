"""Tests for Temporal worker components."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.memorize_activity import _safe_serialize, task_memorize
from app.workers.memorize_workflow import MemorizeWorkflow
from app.workers.worker import TASK_QUEUE, create_temporal_client, run_worker

# ── Activity tests ──


SAMPLE_SPEC = {
    "task_id": "test-task-001",
    "resource_url": "/data/storage/conversation-abc123.json",
    "user_id": "user123",
    "agent_id": "agent456",
}


@pytest.mark.asyncio
async def test_task_memorize_success():
    """Test successful memorize activity execution."""
    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(return_value={"memories_created": 3})

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
    ):
        result = await task_memorize(SAMPLE_SPEC)

    assert result["task_id"] == "test-task-001"
    assert result["status"] == "SUCCESS"
    assert "finished_at" in result
    assert result["result"] == {"memories_created": 3}
    mock_service.memorize.assert_called_once_with(
        resource_url="/data/storage/conversation-abc123.json",
        modality="conversation",
        user={"user_id": "user123", "agent_id": "agent456"},
    )


@pytest.mark.asyncio
async def test_task_memorize_with_override_config():
    """Test memorize activity with override config."""
    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(return_value={})
    mock_settings = MagicMock()

    spec_with_override = {
        **SAMPLE_SPEC,
        "override_config": {"chunk_size": 512},
    }

    with (
        patch("app.workers.memorize_activity.Settings", return_value=mock_settings),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service) as mock_create,
    ):
        await task_memorize(spec_with_override)

    mock_create.assert_called_once_with(
        settings=mock_settings,
        memorize_config={"chunk_size": 512},
    )


@pytest.mark.asyncio
async def test_task_memorize_failure():
    """Test memorize activity handles errors gracefully."""
    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(side_effect=RuntimeError("DB connection failed"))

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
    ):
        result = await task_memorize(SAMPLE_SPEC)

    assert result["task_id"] == "test-task-001"
    assert result["status"] == "FAILURE"
    assert "DB connection failed" in result["error"]
    assert "finished_at" in result


@pytest.mark.asyncio
async def test_task_memorize_default_task_id():
    """Test that missing task_id defaults to 'unknown'."""
    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(return_value={})

    spec_no_id = {k: v for k, v in SAMPLE_SPEC.items() if k != "task_id"}

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
    ):
        result = await task_memorize(spec_no_id)

    assert result["task_id"] == "unknown"
    assert result["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_task_memorize_default_agent_id():
    """Test that missing agent_id defaults to empty string."""
    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(return_value={})

    spec_no_agent = {k: v for k, v in SAMPLE_SPEC.items() if k != "agent_id"}

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
    ):
        await task_memorize(spec_no_agent)

    mock_service.memorize.assert_called_once()
    call_kwargs = mock_service.memorize.call_args[1]
    assert call_kwargs["user"]["agent_id"] == ""


# ── _safe_serialize tests ──


def test_safe_serialize_json_compatible():
    """Test that JSON-compatible objects pass through."""
    data = {"key": "value", "count": 42}
    assert _safe_serialize(data) == data


def test_safe_serialize_non_serializable():
    """Test that non-serializable objects are converted to string."""
    obj = object()
    result = _safe_serialize(obj)
    assert isinstance(result, str)


# ── Workflow tests ──


def test_memorize_workflow_is_registered():
    """Test that MemorizeWorkflow is a valid Temporal workflow."""
    assert hasattr(MemorizeWorkflow, "run")
    assert MemorizeWorkflow.__name__ == "MemorizeWorkflow"


# ── Worker configuration tests ──


def test_task_queue_name():
    """Test task queue constant."""
    assert TASK_QUEUE == "memu-worker"


@pytest.mark.asyncio
async def test_create_temporal_client():
    """Test Temporal client creation with settings."""
    mock_client = MagicMock()

    with patch("app.workers.worker.Client") as mock_client_cls:
        mock_client_cls.connect = AsyncMock(return_value=mock_client)
        settings = MagicMock()
        settings.temporal_url = "localhost:7233"
        settings.TEMPORAL_NAMESPACE = "test-ns"

        client = await create_temporal_client(settings)

    assert client == mock_client
    mock_client_cls.connect.assert_called_once_with(
        "localhost:7233",
        namespace="test-ns",
    )


@pytest.mark.asyncio
async def test_run_worker_registers_workflow_and_activities():
    """Test that worker is configured with correct workflow and activities."""
    mock_client = MagicMock()

    # Make the Future immediately raise CancelledError to break `await asyncio.Future()`
    mock_future = asyncio.Future()
    mock_future.cancel()

    with (
        patch("app.workers.worker.Worker") as mock_worker_cls,
        patch("asyncio.Future", return_value=mock_future),
    ):
        mock_worker_instance = MagicMock()
        mock_worker_instance.__aenter__ = AsyncMock(return_value=mock_worker_instance)
        mock_worker_instance.__aexit__ = AsyncMock(return_value=False)
        mock_worker_cls.return_value = mock_worker_instance

        with pytest.raises(asyncio.CancelledError):
            await run_worker(mock_client)

    mock_worker_cls.assert_called_once()
    call_kwargs = mock_worker_cls.call_args[1]
    assert call_kwargs["task_queue"] == "memu-worker"
    assert MemorizeWorkflow in call_kwargs["workflows"]
    assert task_memorize in call_kwargs["activities"]
    assert call_kwargs["identity"] == TASK_QUEUE
