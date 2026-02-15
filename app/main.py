"""memU Server - FastAPI application entry point."""

import json
import traceback
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.services.memu import create_memory_service
from config.settings import Settings

# Load validated settings from environment / .env
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
storage_dir.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialise MemoryService on startup (defers DB connection until the app runs)."""
    try:
        _app.state.service = create_memory_service(settings)
    except Exception as exc:
        # Log full traceback for operators and wrap in a clearer startup error
        traceback.print_exc()
        msg = "Failed to initialize MemoryService during application startup"
        raise RuntimeError(msg) from exc
    yield


app = FastAPI(title="memU Server", version="0.1.0", lifespan=lifespan)


@app.post("/memorize")
async def memorize(request: Request, payload: dict[str, Any]):
    try:
        service = request.app.state.service
        file_path = storage_dir / f"conversation-{uuid.uuid4().hex}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

        result = await service.memorize(resource_url=str(file_path), modality="conversation")
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/retrieve")
async def retrieve(request: Request, payload: dict[str, Any]):
    if "query" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")
    try:
        service = request.app.state.service
        result = await service.retrieve([payload["query"]])
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
async def root():
    return {"message": "Hello MemU user!"}
