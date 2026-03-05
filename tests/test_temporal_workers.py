"""Tests for Temporal worker components."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.memorize_activity import task_memorize
from app.workers.memorize_workflow import MemorizeWorkflow
from app.workers.worker import TASK_QUEUE, create_temporal_client, run_worker

# ── Activity tests ──


SAMPLE_SPEC = {
    "task_id": "test-task-001",
    "resource_url": "conversation-abc123.json",
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
    mock_service.memorize.assert_called_once()
    call_kwargs = mock_service.memorize.call_args[1]
    # resource_url should be reconstructed as an absolute path under STORAGE_PATH
    assert call_kwargs["resource_url"].endswith("conversation-abc123.json")
    assert call_kwargs["modality"] == "conversation"
    assert call_kwargs["user"] == {"user_id": "user123", "agent_id": "agent456"}


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
    """Test memorize activity raises ApplicationError on failure (without leaking details)."""
    from temporalio.exceptions import ApplicationError

    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(side_effect=RuntimeError("DB connection failed"))

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
        pytest.raises(ApplicationError, match="Memorize activity failed for task"),
    ):
        await task_memorize(SAMPLE_SPEC)


@pytest.mark.asyncio
async def test_task_memorize_missing_required_fields():
    """Test that missing required fields raises non-retryable ApplicationError."""
    from temporalio.exceptions import ApplicationError

    spec_missing = {"task_id": "test-001"}  # missing resource_url and user_id

    with pytest.raises(ApplicationError, match="resource_url") as exc_info:
        await task_memorize(spec_missing)

    assert exc_info.value.non_retryable is True


@pytest.mark.asyncio
async def test_task_memorize_empty_required_fields():
    """Test that empty-string required fields raises non-retryable ApplicationError."""
    from temporalio.exceptions import ApplicationError

    spec_empty = {"task_id": "t1", "resource_url": "", "user_id": "  "}

    with pytest.raises(ApplicationError, match="resource_url") as exc_info:
        await task_memorize(spec_empty)

    assert exc_info.value.non_retryable is True


@pytest.mark.asyncio
async def test_task_memorize_none_required_fields():
    """Test that None-valued required fields raises non-retryable ApplicationError."""
    from temporalio.exceptions import ApplicationError

    spec_none = {"task_id": "t1", "resource_url": None, "user_id": "user1"}

    with pytest.raises(ApplicationError, match="resource_url") as exc_info:
        await task_memorize(spec_none)

    assert exc_info.value.non_retryable is True


@pytest.mark.asyncio
async def test_task_memorize_non_dict_spec():
    """Test that non-dict spec raises non-retryable ApplicationError."""
    from temporalio.exceptions import ApplicationError

    with pytest.raises(ApplicationError, match="spec must be a dict") as exc_info:
        await task_memorize(None)

    assert exc_info.value.non_retryable is True


@pytest.mark.asyncio
async def test_task_memorize_path_traversal_rejected():
    """Test that absolute paths and '..' in resource_url are rejected."""
    from temporalio.exceptions import ApplicationError

    for bad_url in ["/etc/passwd", "../secret.json", "foo/../../etc/passwd"]:
        spec = {**SAMPLE_SPEC, "resource_url": bad_url}
        with (
            patch("app.workers.memorize_activity.Settings"),
            patch("app.workers.memorize_activity.create_memory_service"),
            pytest.raises(ApplicationError, match="unsafe filename") as exc_info,
        ):
            await task_memorize(spec)
        assert exc_info.value.non_retryable is True


@pytest.mark.asyncio
async def test_task_memorize_invalid_override_config():
    """Test that non-dict override_config raises non-retryable ApplicationError."""
    from temporalio.exceptions import ApplicationError

    spec_bad_config = {**SAMPLE_SPEC, "override_config": "not-a-dict"}

    with (
        patch("app.workers.memorize_activity.Settings"),
        pytest.raises(ApplicationError, match="override_config must be a dict") as exc_info,
    ):
        await task_memorize(spec_bad_config)

    assert exc_info.value.non_retryable is True


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


# ── Serialization tests (via public API) ──


@pytest.mark.asyncio
async def test_task_memorize_serializes_result():
    """Test that non-serializable results are safely converted."""

    class NonSerializable:
        def __str__(self) -> str:
            return "custom-result"

    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(return_value=NonSerializable())

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
    ):
        result = await task_memorize(SAMPLE_SPEC)

    # Non-serializable result should be converted to string
    assert isinstance(result["result"], str)


@pytest.mark.asyncio
async def test_task_memorize_passes_serializable_result():
    """Test that JSON-serializable results pass through unchanged."""
    mock_service = MagicMock()
    mock_service.memorize = AsyncMock(return_value={"count": 5})

    with (
        patch("app.workers.memorize_activity.Settings"),
        patch("app.workers.memorize_activity.create_memory_service", return_value=mock_service),
    ):
        result = await task_memorize(SAMPLE_SPEC)

    assert result["result"] == {"count": 5}


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
    assert call_kwargs["identity"].startswith(f"{TASK_QUEUE}@")


@pytest.mark.asyncio
async def test_async_main_validates_openai_api_key():
    """Test that worker startup fails fast when OPENAI_API_KEY is missing."""
    from app.workers.worker import async_main

    mock_settings = MagicMock()
    mock_settings.OPENAI_API_KEY = ""

    with (
        patch("app.workers.worker.Settings", return_value=mock_settings),
        pytest.raises(SystemExit, match="OPENAI_API_KEY"),
    ):
        await async_main()
