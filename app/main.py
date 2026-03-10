"""memU Server - FastAPI application entry point."""

import asyncio
import json
import logging
import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from temporalio.client import Client
from temporalio.service import RPCError, RPCStatusCode

from app.schemas.memory import (
    CategoryObject,
    ClearMemoriesRequest,
    ClearMemoriesResponse,
    ListCategoriesRequest,
    ListCategoriesResponse,
    MemorizeRequest,
    MemorizeResponse,
    TaskStatusResponse,
)
from app.services.memu import create_memory_service
from app.workers.memorize_workflow import MemorizeWorkflow
from app.workers.worker import TASK_QUEUE
from config.settings import Settings

logger = logging.getLogger(__name__)

# Load settings from environment / .env
settings = Settings()

if not settings.OPENAI_API_KEY.strip():
    # EM101/EM102: extract message to variable to satisfy ruff errmsg rules
    msg = (
        "OPENAI_API_KEY environment variable is not set or is empty. "
        "Set OPENAI_API_KEY to a valid OpenAI API key before starting the server."
    )
    raise RuntimeError(msg)

# Storage directory for conversation files
storage_dir = Path(settings.STORAGE_PATH)


async def _get_temporal_client(app: FastAPI) -> Client:
    """Return the cached Temporal client, connecting lazily on first call."""
    # Treat any non-None value as the cached client to support mocking/DI.
    client = getattr(app.state, "temporal", None)
    if client is not None:
        return cast(Client, client)
    # Create the lock lazily on app.state so it's bound to the running event loop
    # (module-level asyncio.Lock() can raise RuntimeError in Python 3.13+).
    lock: asyncio.Lock = getattr(app.state, "_temporal_lock", None) or asyncio.Lock()
    app.state._temporal_lock = lock
    async with lock:
        # Double-check after acquiring the lock
        client = getattr(app.state, "temporal", None)
        if client is not None:
            return cast(Client, client)
        client = await Client.connect(
            settings.temporal_url,
            namespace=settings.TEMPORAL_NAMESPACE,
        )
        app.state.temporal = client
        logger.info("Connected to Temporal at %s", settings.temporal_url)
        return client


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialise MemoryService on startup. Temporal connects lazily on first use."""
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
        _app.state.service = create_memory_service(settings)
    except Exception as exc:
        msg = "Failed to initialize MemoryService during application startup"
        logger.exception(msg)
        raise RuntimeError(msg) from exc
    yield


app = FastAPI(title="memU Server", version="0.1.0", lifespan=lifespan)


@app.post("/memorize")
async def memorize(request: Request, body: MemorizeRequest):
    """Submit an async memorization task via Temporal workflow."""
    file_path: Path | None = None
    workflow_started = False
    try:
        # 1. Save conversation to local storage (offload sync I/O to threadpool)
        task_id = uuid.uuid4().hex
        file_path = storage_dir / f"conversation-{task_id}.json"
        data = json.dumps(body.conversation, ensure_ascii=False)
        await asyncio.to_thread(file_path.write_text, data, "utf-8")

        # 2. Build workflow spec
        # Pass the filename only; the worker reconstructs the full path
        # from its own STORAGE_PATH, so it works across containers/hosts.
        spec = {
            "task_id": task_id,
            "resource_url": file_path.name,
            "user_id": body.user_id,
            "agent_id": body.agent_id,
            "override_config": body.override_config,
        }

        # 3. Start Temporal workflow
        temporal = await _get_temporal_client(request.app)
        workflow_id = f"memorize-{task_id}"

        await temporal.start_workflow(
            MemorizeWorkflow.run,
            spec,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
        workflow_started = True

        logger.info("Memorize workflow started: %s", workflow_id)

        result = MemorizeResponse(
            task_id=workflow_id,
            status="PENDING",
            message=f"Memorization task submitted for user {body.user_id}",
        )
        return JSONResponse(content={"status": "success", "result": result.model_dump()})
    except Exception as exc:
        # Only clean up the conversation file if the workflow has NOT started,
        # because a running workflow still needs its input file.
        if not workflow_started and file_path is not None and file_path.exists():
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                logger.warning(
                    "Failed to clean up conversation file %s during error handling",
                    file_path,
                    exc_info=True,
                )
        logger.exception("Failed to submit memorize task")
        raise HTTPException(status_code=500, detail="Failed to submit memorization task") from exc


# Regex for valid memorize workflow IDs: memorize-<32 hex chars>
_MEMORIZE_WORKFLOW_ID_RE = re.compile(r"^memorize-[0-9a-f]{32}$")


@app.get("/memorize/status/{task_id}")
async def get_memorize_status(request: Request, task_id: str):
    """Get the status of a memorization task."""
    if not _MEMORIZE_WORKFLOW_ID_RE.match(task_id):
        raise HTTPException(
            status_code=422,
            detail="task_id must match the format 'memorize-<uuid4hex>' (e.g. memorize-abc123def456...)",
        )
    try:
        temporal = await _get_temporal_client(request.app)
        handle = temporal.get_workflow_handle(task_id)

        describe = await handle.describe()
        status = describe.status.name if describe.status else "UNKNOWN"

        detail = None
        if status == "COMPLETED":
            result = await handle.result()
            if isinstance(result, dict):
                detail = result.get("status", "SUCCESS")
            elif result is not None:
                detail = str(result)
            else:
                detail = "SUCCESS"
        elif status == "FAILED":
            detail = "Task execution failed"

        task_status = TaskStatusResponse(
            task_id=task_id,
            status=status,
            detail=detail,
        )
        return JSONResponse(content={"status": "success", "result": task_status.model_dump()})
    except RPCError as exc:
        if exc.status == RPCStatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found") from exc
        logger.exception("Temporal RPC error for task %s", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
    except Exception as exc:
        logger.exception("Failed to get task status for %s", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/retrieve")
async def retrieve(request: Request, payload: dict[str, Any]):
    if "query" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")
    query = payload["query"]
    if not isinstance(query, str) or not query.strip():
        raise HTTPException(status_code=400, detail="'query' must be a non-empty string")
    try:
        service = request.app.state.service
        result = await service.retrieve([query.strip()])
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        logger.exception("Retrieve request failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/clear")
async def clear_memory(request: Request, body: ClearMemoriesRequest):
    """Clear memories for a user/agent."""
    try:
        service = request.app.state.service
        where = body.model_dump(exclude_none=True)
        result = await service.clear_memory(where=where)

        response = ClearMemoriesResponse(
            purged_categories=len(result.get("deleted_categories", [])),
            purged_items=len(result.get("deleted_items", [])),
            purged_resources=len(result.get("deleted_resources", [])),
        )
        return JSONResponse(content={"status": "success", "result": response.model_dump()})
    except Exception as exc:
        logger.exception("Clear memory request failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/categories")
async def list_categories(request: Request, body: ListCategoriesRequest):
    """List all memory categories for a user."""
    try:
        service = request.app.state.service
        where = body.model_dump(exclude_none=True)
        result = await service.list_memory_categories(where=where)

        response = ListCategoriesResponse(
            categories=[
                CategoryObject(
                    name=cat["name"],
                    description=cat["description"],
                    user_id=cat["user_id"],
                    agent_id=cat["agent_id"],
                    summary=cat.get("summary"),
                )
                for cat in result.get("categories", [])
            ]
        )
        return JSONResponse(content={"status": "success", "result": response.model_dump()})
    except Exception as exc:
        logger.exception("List categories request failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.get("/")
async def root():
    return {"message": "Hello MemU user!"}
