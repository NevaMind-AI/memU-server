# memU-server: Local Backend Service for AI Memory System

memU-server is the backend management service for MemU, responsible for providing API endpoints, data storage, and management capabilities, as well as deep integration with the core memU framework. It powers the frontend memU-ui with reliable data support, ensuring efficient reading, writing, and maintenance of Agent memories. memU-server can be deployed locally or in private environments and supports quick startup and configuration via Docker, enabling developers to manage the AI memory system in a secure environment.

- Core Algorithm 👉 memU: https://github.com/NevaMind-AI/memU
- One call = response + memory 👉 memU Response API: https://memu.pro/docs#responseapi
- Try it instantly 👉 https://app.memu.so/quick-start

---
## ✨ Features

- 🧠 **Memorize**: Store and process conversational memories asynchronously
- 🔍 **Retrieve**: Query and retrieve relevant memories with semantic search
- 🚀 **Async First**: Built with FastAPI and async/await for high performance
- 🗄️ **PostgreSQL + pgvector**: Vector similarity search with efficient indexing
- ⚡ **Temporal Workflows**: Reliable async task orchestration
- 🔧 **Type Safe**: Full type hints with Pydantic and SQLModel
- 🧪 **Well Tested**: Comprehensive test coverage with pytest

## 🏗️ Architecture

- **Web Framework**: FastAPI with async/await
- **Database**: PostgreSQL 16 with pgvector extension
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Workflow Engine**: Temporal for async task processing
- **Memory Engine**: memu-py for intelligent memory management
- **Migrations**: Alembic for database schema management

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/NevaMind-AI/memU-server.git
cd memU-server
```

2. **Set up Python environment**
```bash
# Create virtual environment with uv (recommended)
uv venv
source .venv/bin/activate

# Or with standard venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
# With uv (fast)
uv pip install -e .

# Or with pip
pip install -e .
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start infrastructure services**
```bash
docker compose up -d
```

This will start:
- PostgreSQL with pgvector on port 54320
- Temporal server on ports 17233 (gRPC) and 18233 (Web UI)

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Start the server**
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or in background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

The API will be available at:
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Alternative Docs (ReDoc): http://localhost:8000/redoc

## 📝 Configuration

Key environment variables in \`.env\`:

```bash
# Database
DATABASE_HOST=localhost
DATABASE_PORT=54320
DATABASE_USER=memu_user
DATABASE_PASSWORD=memu_pass
DATABASE_NAME=memu_db

# Temporal
TEMPORAL_HOST=localhost
TEMPORAL_PORT=17233
TEMPORAL_NAMESPACE=default

# LLM
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_LLM_MODEL=gpt-4o-mini

# Embedding
EMBEDDING_API_KEY=your_embedding_key_here
EMBEDDING_BASE_URL=https://api.voyageai.com/v1
EMBEDDING_MODEL=voyage-3.5-lite

# Storage
STORAGE_PATH=/var/data/memu-server
```

## 🧪 Testing

Run tests with pytest or make:

```bash
# Run all tests
pytest

# Or use make command
make test

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v
```

## 🔧 Code Quality

### Automated Quality Checks

This project uses multiple layers of quality assurance:

**1. Pre-commit Hooks** (Recommended)

Install pre-commit hooks to automatically check code before every commit:

```bash
# Install pre-commit hooks
make pre-commit-install

# Now hooks will run automatically on git commit
# To manually run on all files:
make pre-commit-run
```

**2. Manual Quality Checks**

```bash
# Show all available commands
make help

# Run all quality checks (format, lint, test)
make check

# Format code with ruff
make format

# Check formatting without changes
make format-check

# Lint code
make lint

# Run tests
make test

# Clean cache files
make clean
```

**3. CI/CD Pipeline**

GitHub Actions automatically runs quality checks on:
- Every push to `main`, `develop`, or `feature/**` branches
- Every pull request

### Best Practices

**Before committing code:**
```bash
# Option 1: Let pre-commit hooks handle it (recommended)
git add .
git commit -m "your message"  # Hooks run automatically

# Option 2: Run checks manually first
make check
git add .
git commit -m "your message"
```

**Pre-commit hooks will:**
- ✅ Format code with ruff
- ✅ Fix common issues automatically
- ✅ Check YAML, JSON, TOML syntax
- ✅ Detect private keys and large files
- ✅ Trim whitespace and fix line endings
- ❌ Block commit if critical issues found

**What gets checked:**
- Code formatting (ruff format)
- Linting rules (ruff check)
- File syntax (YAML, JSON, TOML)
- Security issues (private keys)
- File size limits
- Merge conflicts

**Before committing code, always run:**
```bash
make check
```

This will ensure your code is properly formatted, linted, and all tests pass.

## 🗃️ Database Models

### Memory
Stores individual memory entries with vector embeddings for semantic search.

### MemoryCategory
Organizes memories into categories with metadata.

### MemorizeTask
Tracks async memory processing tasks with status and results.

## 🔄 API Endpoints

### Memorize
```bash
POST /memorize
```
Store new memory asynchronously.

### Retrieve
```bash
POST /retrieve
```
Query and retrieve relevant memories.

### Health Check
```bash
GET /
```
Returns service status.

## 🛠️ Development

### Project Structure
```
memU-server/
├── app/
│   ├── api/          # API routes
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   ├── workers/      # Temporal workers
│   ├── utils/        # Utilities
│   ├── database.py   # Database configuration
│   └── main.py       # FastAPI application
├── config/
│   └── settings.py   # Configuration management
├── tests/            # Test suite
├── alembic/          # Database migrations
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### Code Quality

```bash
# Format code with ruff
ruff format .

# Lint code
ruff check .

# Type checking (if mypy is installed)
mypy app/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## 🐳 Docker

Build and run with Docker:

```bash
# Build image
docker build -f dockerfiles/Dockerfile -t memu-server .

# Run container
docker run -d \
  --name memu-server \
  -p 8000:8000 \
  --env-file .env \
  memu-server
```

## 📊 Monitoring

- **Temporal Web UI**: http://localhost:18233
- **Database**: Connect to PostgreSQL on port 54320

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (\`git checkout -b feature/amazing-feature\`)
3. Commit your changes (\`git commit -m 'feat: add amazing feature'\`)
4. Push to the branch (\`git push origin feature/amazing-feature\`)
5. Open a Pull Request

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [memu-py](https://github.com/mem0ai/memu-py) - Core memory management engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Temporal](https://temporal.io/) - Workflow orchestration
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search
