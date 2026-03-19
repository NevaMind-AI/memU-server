# memU-server: Local Backend Service for AI Memory System

memU-server is the backend management service for MemU, responsible for providing API endpoints, data storage, and management capabilities, as well as deep integration with the core memU framework. It powers the frontend memU-ui with reliable data support, ensuring efficient reading, writing, and maintenance of Agent memories. memU-server can be deployed locally or in private environments and supports quick startup and configuration via Docker, enabling developers to manage the AI memory system in a secure environment.

- Core Algorithm 👉 memU: https://github.com/NevaMind-AI/memU
- One call = response + memory 👉 memU Response API: https://memu.pro/docs#responseapi
- Try it instantly 👉 https://app.memu.so/quick-start

---

## ⭐ Star Us on GitHub

Star memU-server to get notified about new releases and join our growing community of AI developers building intelligent agents with persistent memory capabilities.
💬 Join our Discord community: https://discord.gg/memu

---

## 🏗️ Architecture

memU-server runs as two cooperating processes backed by shared infrastructure:

```
                          ┌─────────────────────────────────────┐
  Client ──HTTP──►        │  FastAPI API Server  (port 8000)    │
                          │  POST /memorize  →  start workflow  │
                          │  GET  /memorize/status/{task_id}    │
                          │  POST /retrieve, /clear, /categories│
                          └──────────────┬──────────────────────┘
                                         │ gRPC
                          ┌──────────────▼──────────────────────┐
                          │      Temporal Server (port 7233)     │
                          └──────────────┬──────────────────────┘
                                         │ poll
                          ┌──────────────▼──────────────────────┐
                          │       Temporal Worker Process        │
                          │  MemorizeWorkflow → task_memorize   │
                          │  (calls memu-py MemoryService)      │
                          └──────────────┬──────────────────────┘
                                         │ SQL
                          ┌──────────────▼──────────────────────┐
                          │  PostgreSQL + pgvector  (port 5432)  │
                          │  app db: memu  |  temporal db: temporal│
                          └─────────────────────────────────────┘
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Server | FastAPI 0.122+ / Python 3.13 | HTTP endpoints, request validation, workflow dispatch |
| Workflow Engine | Temporal 1.25 / temporalio SDK 1.16 | Durable async task orchestration for `/memorize` |
| Worker | Temporal Worker (same codebase) | Executes `MemorizeWorkflow` → `task_memorize` activity |
| Database | PostgreSQL 16 + pgvector | Vector storage for memories, Temporal persistence |
| Memory Core | memu-py 1.2+ | Three-layer memory algorithm (Resource → Item → Category) |

### How `/memorize` Works (Async)

1. Client POSTs conversation payload to `/memorize`.
2. API server saves conversation to local storage, starts a Temporal workflow, and returns immediately with a `task_id`.
3. Temporal dispatches the `MemorizeWorkflow` to the worker process.
4. The worker executes `task_memorize` activity (calls memu-py `MemoryService.memorize()`), writing results to PostgreSQL.
5. Client polls `GET /memorize/status/{task_id}` to track progress (`RUNNING` → `COMPLETED` / `FAILED`).

---

## 🚀 Get Started

### Prerequisites

- **Python 3.13+** and [uv](https://docs.astral.sh/uv/) package manager
- **Docker & Docker Compose** (for infrastructure services)
- **OpenAI API key** (required for LLM and embedding operations)

### 1. Start Infrastructure

Launch PostgreSQL (with pgvector), Temporal Server, and Temporal UI:

```bash
docker compose up -d
```

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database with pgvector extension |
| Temporal | 7233 | Workflow engine gRPC API |
| Temporal UI | 8088 | Web management interface |

### 2. Install & Run from Source

```bash
# Clone the repository
git clone https://github.com/NevaMind-AI/memU-server.git
cd memU-server

# Install dependencies
make install
# or: uv sync

# Configure environment (create .env or export)
export OPENAI_API_KEY=your_api_key_here

# Start the API server (terminal 1)
make run
# or: uv run fastapi dev

# Start the Temporal worker (terminal 2)
uv run python -m app.workers.worker
```

The API server runs on `http://127.0.0.1:8000`.

### 3. Run with Docker

```bash
export OPENAI_API_KEY=your_api_key_here

# Pull and run the API server
docker pull nevamindai/memu-server:latest

docker run --rm -p 8000:8000 \
  --network memu-network \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e POSTGRES_HOST=postgres \
  -e TEMPORAL_HOST=temporal \
  nevamindai/memu-server:latest
```

> **Note:** Both the API server and Temporal worker share the same Docker image. Override the entrypoint to run the worker:
> ```bash
> docker run --rm \
>   --network memu-network \
>   -e OPENAI_API_KEY=$OPENAI_API_KEY \
>   -e POSTGRES_HOST=postgres \
>   -e TEMPORAL_HOST=temporal \
>   nevamindai/memu-server:latest \
>   uv run python -m app.workers.worker
> ```

### Environment Variables

The memU-server API and worker processes load their configuration from environment variables or an `.env` file. Key application-level variables:

> Docker Compose may define additional infrastructure-specific environment variables (for example, `TEMPORAL_DB`); refer to `docker-compose.yml` for the complete list used by the containers.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL |
| `DEFAULT_LLM_MODEL` | `gpt-4o-mini` | Chat model for memorization |
| `EMBEDDING_API_KEY` | Falls back to `OPENAI_API_KEY` | Embedding provider API key |
| `EMBEDDING_BASE_URL` | `https://api.voyageai.com/v1` | Embedding API base URL |
| `EMBEDDING_MODEL` | `voyage-3.5-lite` | Embedding model name |
| `POSTGRES_USER` | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL password |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `memu` | Application database name |
| `DATABASE_URL` | *(auto-assembled)* | Full DSN (overrides individual PG vars) |
| `TEMPORAL_HOST` | `localhost` | Temporal server host |
| `TEMPORAL_PORT` | `7233` | Temporal server gRPC port |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `STORAGE_PATH` | `./data/storage` | Local directory for conversation files |

### Makefile Commands

```bash
make install       # Install dependencies & pre-commit hooks
make run           # Start FastAPI dev server
make check         # Lint + type check + dependency check (CI)
make test          # Run tests with coverage
make clean         # Clean __pycache__, .pyc, build artifacts
make docker-up     # Start Docker infrastructure services
make docker-down   # Stop Docker infrastructure services
```

---

## 📡 API Endpoints

### `GET /` — Health Check

```bash
curl http://localhost:8000/
```

Response: `{"message": "Hello MemU user!"}`

### `POST /memorize` — Submit Async Memorization Task

Saves conversation data and starts an async Temporal workflow. Returns immediately with a `task_id` for status polling.

**Request:**
```json
{
  "conversation": [
    {"role": "user", "content": {"text": "I prefer dark mode"}, "created_at": "2025-03-20 10:00:00"},
    {"role": "assistant", "content": {"text": "Noted!"}, "created_at": "2025-03-20 10:00:01"}
  ],
  "user_id": "user-001",
  "agent_id": "agent-001",
  "override_config": null
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "task_id": "memorize-a1b2c3d4e5f60718293a4b5c6d7e8f90",
    "status": "PENDING",
    "message": "Memorization task submitted for user user-001"
  }
}
```

### `GET /memorize/status/{task_id}` — Poll Task Status

Track a memorization task. The `task_id` must match the format `memorize-<32 hex chars>` (as returned by `POST /memorize`).

```bash
curl http://localhost:8000/memorize/status/memorize-a1b2c3d4e5f60718293a4b5c6d7e8f90
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "task_id": "memorize-a1b2c3d4e5f60718293a4b5c6d7e8f90",
    "status": "COMPLETED",
    "detail": "SUCCESS"
  }
}
```

Status values: `RUNNING`, `COMPLETED`, `FAILED`, `CANCELED`, `TERMINATED`, `UNKNOWN`.

### `POST /retrieve` — Query Stored Memories

```json
{"query": "What are the user's UI preferences?"}
```

**Response:**
```json
{
  "status": "success",
  "result": { ... }
}
```

### `POST /clear` — Clear Memories

Delete memories for a specific user and/or agent. At least one of `user_id` or `agent_id` must be provided.

```json
{"user_id": "user-001", "agent_id": "agent-001"}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "purged_categories": 3,
    "purged_items": 15,
    "purged_resources": 2
  }
}
```

### `POST /categories` — List Memory Categories

List all memory categories for a user.

```json
{"user_id": "user-001"}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "categories": [
      {
        "name": "UI Preferences",
        "description": "User interface preferences",
        "user_id": "user-001",
        "agent_id": "agent-001",
        "summary": "User prefers dark mode..."
      }
    ]
  }
}
```

---

## 🔌 Integration Guide

### Python

```python
import httpx

BASE = "http://localhost:8000"

# Memorize a conversation
resp = httpx.post(f"{BASE}/memorize", json={
    "conversation": [
        {"role": "user", "content": {"text": "I like Python"}, "created_at": "2025-03-20 10:00:00"},
        {"role": "assistant", "content": {"text": "Great choice!"}, "created_at": "2025-03-20 10:00:01"},
    ],
    "user_id": "user-001",
})
task_id = resp.json()["result"]["task_id"]

# Poll until complete
import time
while True:
    status = httpx.get(f"{BASE}/memorize/status/{task_id}").json()
    if status["result"]["status"] in ("COMPLETED", "FAILED"):
        break
    time.sleep(2)

# Retrieve memories
result = httpx.post(f"{BASE}/retrieve", json={"query": "What languages does the user like?"})
print(result.json())
```

### cURL

```bash
# Submit memorization
curl -X POST http://localhost:8000/memorize \
  -H "Content-Type: application/json" \
  -d '{"conversation": [{"role":"user","content":{"text":"hello"},"created_at":"2025-01-01 00:00:00"}], "user_id":"u1"}'

# Check status (use the task_id returned by POST /memorize)
curl http://localhost:8000/memorize/status/<task_id>

# Retrieve
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "user preferences"}'

# List categories
curl -X POST http://localhost:8000/categories \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1"}'

# Clear memories
curl -X POST http://localhost:8000/clear \
  -H "Content-Type: application/json" \
  -d '{"user_id": "u1"}'
```

---

## 🔑 Key Features

### Async Memorization with Temporal
- Non-blocking `/memorize` endpoint returns immediately with a task ID
- Durable workflow execution — tasks survive server restarts
- Status tracking via `/memorize/status/{task_id}`
- 10-minute activity timeout with automatic retry support

### Quick Deployment
- Docker image for both API server and worker
- Docker Compose for infrastructure (PostgreSQL + Temporal)
- Single `make install && make run` to start development

### Comprehensive Memory Management
- **Memorize**: Async conversation ingestion via Temporal workflows
- **Retrieve**: Semantic search over stored memories (RAG-based or LLM-based)
- **Clear**: Targeted memory deletion by user/agent
- **Categories**: Browse and manage memory categories

---

## 🧩 Why MemU?

Most memory systems in current LLM pipelines rely heavily on explicit modeling, requiring manual definition and annotation of memory categories. This limits AI’s ability to truly understand memory and makes it difficult to support diverse usage scenarios.

MemU offers a flexible and robust alternative, inspired by hierarchical storage architecture in computer systems. It progressively transforms heterogeneous input data into queryable and interpretable textual memory.

Its core architecture consists of three layers: **Resource Layer → Memory Item Layer → MemoryCategory Layer**.

<img width="1363" height="563" alt="Three-Layer Architecture Diagram" src="https://github.com/user-attachments/assets/2803b54a-7595-42f7-85ad-1ea505a6d57c" />

- Resource Layer: Multimodal raw data warehouse
- Memory Item Layer: Discrete extracted memory units
- MemoryCategory Layer: Aggregated textual memory units

### Key Features:
- Full Traceability: Track from raw data → items → documents and back
- Memory Lifecycle: Memorization → Retrieval → Self-evolution
- Two Retrieval Methods:
  - RAG-based: Fast embedding vector search
  - LLM-based: Direct file reading with deep semantic understanding
- Self-Evolving: Adapts memory structure based on usage patterns

<img width="1365" height="308" alt="process" src="https://github.com/user-attachments/assets/3c5ce3ff-14c0-4d2d-aec7-c93f04a1f3e4" />

---

## 📄 License

By contributing to memU-server, you agree that your contributions will be licensed under the **AGPL-3.0 License**.

---

## 🌍 Community

For more information please contact info@nevamind.ai

- GitHub Issues: Report bugs, request features, and track development. [Submit an issue](https://github.com/NevaMind-AI/memU-server/issues)
- Discord: Get real-time support, chat with the community, and stay updated. [Join us](https://discord.com/invite/hQZntfGsbJ)
- X (Twitter): Follow for updates, AI insights, and key announcements. [Follow us](https://x.com/memU_ai)
