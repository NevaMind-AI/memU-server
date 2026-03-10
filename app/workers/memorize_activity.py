"""Temporal activity for memorize task execution."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.services.memu import create_memory_service
from config.settings import Settings

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ("resource_url", "user_id")


@activity.defn(name="task_memorize")
async def task_memorize(spec: dict) -> dict[str, Any]:
    """Execute memorization via memu-py MemoryService.

    Args:
        spec: Dict containing task_id, resource_url, user_id, agent_id, etc.

    Returns:
        Dict with finished_at timestamp and status.

    Raises:
        ApplicationError: If required fields are missing or empty (non-retryable).
        ApplicationError: If memorization fails.
    """
    task_id = spec.get("task_id", "unknown") if isinstance(spec, dict) else "unknown"

    # Validate spec is a dict
    if not isinstance(spec, dict):
        raise ApplicationError(
            f"spec must be a dict, got {type(spec).__name__}",
            non_retryable=True,
        )

    # Validate required fields up front (must be present, string, and non-empty)
    missing: list[str] = []
    for field in _REQUIRED_FIELDS:
        value = spec.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
    if missing:
        msg = f"Missing or empty required field(s) in spec: {', '.join(missing)}"
        raise ApplicationError(msg, non_retryable=True)

    logger.info("Starting memorize activity for task %s", task_id)

    try:
        settings = Settings()

        # Validate override_config type if provided
        override_config = spec.get("override_config")
        if override_config is not None and not isinstance(override_config, dict):
            msg = f"override_config must be a dict, got {type(override_config).__name__}"
            raise ApplicationError(msg, non_retryable=True)

        # Validate and resolve resource_url BEFORE building the service so
        # invalid specs fail fast without opening DB connections or other resources.
        raw_url = spec["resource_url"]
        candidate = Path(raw_url)
        # Reject absolute paths, path traversal, and any directory components.
        # candidate.name != raw_url catches inputs like "subdir/file.json".
        if candidate.is_absolute() or ".." in candidate.parts or candidate.name != raw_url:
            raise ApplicationError(
                "Invalid resource_url: must be a bare filename without path separators",
                non_retryable=True,
            )
        resource_url = str(Path(settings.STORAGE_PATH).resolve() / candidate.name)

        # Build MemoryService with optional config override
        if override_config:
            service = create_memory_service(
                settings=settings,
                memorize_config=override_config,
            )
        else:
            service = create_memory_service(settings=settings)

        # Execute memorization
        result = await service.memorize(
            resource_url=resource_url,
            modality="conversation",
            user={
                "user_id": spec["user_id"],
                "agent_id": spec.get("agent_id", ""),
            },
        )

        finished_at = datetime.now(UTC).isoformat()
        logger.info("Memorize activity completed for task %s", task_id)

        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "finished_at": finished_at,
            "result": _safe_serialize(result),
        }

    except ApplicationError:
        raise
    except Exception as e:
        logger.exception("Memorize activity failed for task %s: %r", task_id, e)
        # Raise with generic message to avoid leaking sensitive info into Temporal history
        raise ApplicationError(f"Memorize activity failed for task {task_id}") from e


def _safe_serialize(obj: Any) -> Any:
    """Safely serialize result to JSON-compatible format."""
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)
