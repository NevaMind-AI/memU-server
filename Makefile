.PHONY: help install dev clean run docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make dev          - Install dev dependencies"
	@echo "  make clean        - Clean cache and build files"
	@echo "  make run          - Run the development server"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"

# Install production dependencies
install:
	uv sync --no-dev

# Install development dependencies
dev:
	uv sync

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
	uv run fastapi dev

# Start Docker services
docker-up:
	@if [ ! -f docker-compose.yml ] && [ ! -f docker-compose.yaml ]; then \
		echo "⚠️  Docker compose configuration not found in this repository."; \
		echo "Please add a docker-compose.yml/docker-compose.yaml file or update the 'docker-up' target."; \
		exit 1; \
	fi
	docker compose up -d

# Stop Docker services
docker-down:
	@if [ ! -f docker-compose.yml ] && [ ! -f docker-compose.yaml ]; then \
		echo "⚠️  Docker compose configuration not found in this repository."; \
		echo "Please add a docker-compose.yml/docker-compose.yaml file or update the 'docker-down' target."; \
		exit 1; \
	fi
	docker compose down
