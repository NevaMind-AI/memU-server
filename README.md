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

## 🚀 Get Started

### Run from source
1. Ensure you have Python 3.13+ and [uv](https://docs.astral.sh/uv/) installed.
2. Clone the repository and enter it:
   ```bash
   git clone https://github.com/NevaMind-AI/memU-server.git
   cd memU-server
   ```
3. Set your OpenAI API key in the environment:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
4. Install dependencies and start the FastAPI dev server:
   ```bash
   uv sync
   uv run fastapi dev
   ```
   The server runs on `http://127.0.0.1:8000`.

### Run with Docker Compose (Local Development)
Start the full local development environment with PostgreSQL and Temporal:

```bash
# Start all services (PostgreSQL, Temporal, Temporal UI)
docker compose up -d

# View logs
docker compose logs -f
```

**Services:**
| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database with pgvector extension |
| Temporal | 7233 | Workflow engine gRPC API |
| Temporal UI | 8088 | Web management interface |

**Default Configuration:**
- PostgreSQL DSN: `postgresql://postgres:postgres@localhost:5432/memu`
- Temporal Database: `temporal` (separate from app database)

**Environment Variables (optional `.env` file):**
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=memu
TEMPORAL_DB=temporal
```

### Run with Docker
1. Export your OpenAI API key so Docker can read it:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
2. Pull the latest image:
   ```bash
   docker pull nevamindai/memu-server:latest
   ```
3. Start the container (optionally mount a host directory to persist `./data`):
   ```bash
   docker run --rm -p 8000:8000 \
     -e OPENAI_API_KEY=$OPENAI_API_KEY \
     nevamindai/memu-server:latest
   ```
   Access the API at `http://127.0.0.1:8000`.

### API Endpoints
- `POST /memorize`: persist a conversation-style payload for later retrieval. Example body shape:
  ```json
  {
    "content": [
      {"role": "user", "content": {"text": "..."}, "created_at": "YYYY-MM-DD HH:MM:SS"},
      {"role": "assistant", "content": {"text": "..."}, "created_at": "YYYY-MM-DD HH:MM:SS"}
    ]
  }
  ```
- `POST /retrieve`: query stored memories with a text prompt:
  ```json
  {"query": "your question about the conversation"}
  ```
- To smoke-test locally, set `MEMU_API_URL` (defaults to `http://127.0.0.1:12345`), POST a conversation to `/memorize`, then call `/retrieve` with a text query.

---

## 🔑 Key Features

### Quick Deployment
- Docker image provided
- Launch backend service and database with a single command
- Provides API endpoints compatible with memU-ui, ensuring stable and reliable data services

### Comprehensive Memory Management
(Some features planned for future releases)
- Memory Data Management
  - Support creating, reading, and deleting Memory Submissions
  - Memorize results support create, read, update, and delete (CRUD) operations
  - Retrieve records support querying and tracking
  - Tracks LLM token usage for transparent and controllable costs
- User and Permission Management
  - User login and registration system
  - Role-based access control: Developer / Admin / Regular User
  - Backend manages access scope and permissions for secure operations

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
