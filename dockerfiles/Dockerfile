FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY uv.lock pyproject.toml README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application code
COPY . .

# Sync the project
RUN uv sync --frozen --no-dev

# Expose the port that FastAPI will run on
EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"

CMD [ \
  "python", "-m", "gunicorn", \
  "--bind", "0.0.0.0:8000", \
  "--worker-class", "uvicorn.workers.UvicornWorker", \
  "app.main:app" \
]
