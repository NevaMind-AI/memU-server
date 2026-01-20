import json
import os
from pathlib import Path
import traceback
from typing import Any, Dict
import uuid
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from memu.app import MemoryService

app = FastAPI(title="memU Server", version="0.1.0")

# Initialize MemoryService with proper configuration
service = MemoryService(
    llm_profiles={
        "default": {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "model": os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        }
    },
    database_config={
        "url": f"postgresql+psycopg://{os.getenv('DATABASE_USER', 'memu_user')}:"
               f"{os.getenv('DATABASE_PASSWORD', 'memu_pass')}@"
               f"{os.getenv('DATABASE_HOST', 'localhost')}:"
               f"{os.getenv('DATABASE_PORT', '54320')}/"
               f"{os.getenv('DATABASE_NAME', 'memu_db')}"
    }
)

storage_dir = Path(os.getenv("STORAGE_PATH", "./data"))
storage_dir.mkdir(parents=True, exist_ok=True)

@app.post("/memorize")
async def memorize(payload: Dict[str, Any]):
    try:
        file_path = storage_dir / f"conversation-{uuid.uuid4().hex}.json"
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

        result = await service.memorize(resource_url=str(file_path), modality="conversation")
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/retrieve")
async def retrieve(payload: Dict[str, Any]):
    if "query" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'query' in request body")
    try:
        result = await service.retrieve([payload["query"]])
        return JSONResponse(content={"status": "success", "result": result})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/")
async def root():
    return {"message": "Hello MemU user!"}
