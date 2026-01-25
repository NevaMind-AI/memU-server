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
storage_dir = Path(os.getenv("STORAGE_PATH", "./data"))
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


@app.get("/")
async def root():
    return {"message": "Hello MemU user!"}
