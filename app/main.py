import json
import os
import traceback
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from memu.app import MemoryService

from app.database import get_database_url
from app.schemas.memory import (
    CategoryObject,
    ClearMemoriesRequest,
    ClearMemoriesResponse,
    ListCategoriesRequest,
    ListCategoriesResponse,
)

app = FastAPI(title="memU Server", version="0.1.0")

# Ensure required environment variables are set
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable is not set or is empty. "
        "Set OPENAI_API_KEY to a valid OpenAI API key before starting the server."
    )

# Get database URL using shared configuration utility
database_url = get_database_url()

service = MemoryService(
    llm_profiles={
        "default": {
            "provider": "openai",
            "api_key": openai_api_key,
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
        }
    },
    database_config={"url": database_url},
)

# Storage directory for conversation files
# Support both new STORAGE_PATH and legacy MEMU_STORAGE_DIR for backward compatibility
storage_dir = Path(os.getenv("STORAGE_PATH") or os.getenv("MEMU_STORAGE_DIR") or "./data")
storage_dir.mkdir(parents=True, exist_ok=True)


@app.post("/memorize")
async def memorize(payload: dict[str, Any]):
    try:
        file_path = storage_dir / f"conversation-{uuid.uuid4().hex}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

        result = await service.memorize(resource_url=str(file_path), modality="conversation")
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/retrieve")
async def retrieve(payload: dict[str, Any]):
    if "query" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")
    try:
        result = await service.retrieve([payload["query"]])
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/clear")
async def clear_memory(request: ClearMemoriesRequest):
    """Clear memories for a user/agent."""
    try:
        where = request.model_dump(exclude_none=True)
        result = await service.clear_memory(where=where)

        return ClearMemoriesResponse(
            purged_categories=len(result.get("deleted_categories", [])),
            purged_items=len(result.get("deleted_items", [])),
            purged_resources=len(result.get("deleted_resources", [])),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {e!s}") from e


@app.post("/categories")
async def list_categories(request: ListCategoriesRequest):
    """List all memory categories for a user."""
    try:
        where = request.model_dump(exclude_none=True)
        result = await service.list_memory_categories(where=where)

        return ListCategoriesResponse(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {e!s}") from e


@app.get("/")
async def root():
    return {"message": "Hello MemU user!"}
