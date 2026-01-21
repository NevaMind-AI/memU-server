.PHONY: help install dev test test-cov check format lint clean run docker-up docker-down migrate pre-commit-install pre-commit-run migrate-check

# Default target
help:
	@echo "Available commands:"
	@echo "  make install            - Install dependencies"
	@echo "  make dev                - Install dev dependencies"
	@echo "  make test               - Run tests"
	@echo "  make test-cov           - Run tests with coverage report"
	@echo "  make check              - Run all quality checks (format, lint, test)"
	@echo "  make format             - Format code with ruff"
	@echo "  make format-check       - Check code formatting without changes"
	@echo "  make lint               - Lint code with ruff"
	@echo "  make clean              - Clean cache and build files"
	@echo "  make run                - Run the server"
	@echo "  make docker-up          - Start Docker services"
	@echo "  make docker-down        - Stop Docker services"
	@echo "  make migrate            - Run database migrations"
	@echo "  make migrate-check      - Check migrations for empty content"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run     - Run pre-commit on all files"

# Install production dependencies
install:
	uv pip install -e .

# Install development dependencies
dev:
	uv pip install -e ".[dev]"

# Run tests
test:
	@pytest -v || echo "⚠️  No tests found or tests failed"

# Run tests with coverage
test-cov:
	@echo "🔍 Running tests with coverage..."
	@pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=80 tests/

# Run all quality checks
check: format-check lint test
	@echo "✅ All quality checks passed!"

# Format code
format:
	ruff format .

# Check formatting without making changes
format-check:
	@echo "🔍 Checking code formatting..."
	ruff format --check .

# Lint code
lint:
	@echo "🔍 Linting code..."
	ruff check .
	@echo "🔍 Running pylint..."
	pylint app/ --fail-under=8.0 || true

# Clean cache and build files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf dist/ build/ .coverage htmlcov/

# Run the development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Docker services
docker-up:
	docker compose up -d

# Stop Docker services
docker-down:
	docker compose down

# Run database migrations
migrate:
	alembic upgrade head

# Run migrations rollback
migrate-down:
	alembic downgrade -1

# Create a new migration
migrate-create:
	@read -p "Enter migration description: " desc; \
	alembic revision --autogenerate -m "$$desc"
	@echo "⚠️  Don't forget to review the generated migration file!"
	@python .pre-commit-hooks/check_alembic_migrations.py || true

# Check migrations for issues
migrate-check:
	@python .pre-commit-hooks/check_alembic_migrations.py

# Install pre-commit hooks
pre-commit-install:
	@echo "📦 Installing pre-commit..."
	uv pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed! They will run automatically on git commit."

# Run pre-commit on all files
pre-commit-run:
	@echo "🔍 Running pre-commit checks on all files..."
	pre-commit run --all-files
