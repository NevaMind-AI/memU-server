"""Database configuration utilities.

This module provides helper functions for constructing database connection URLs.
Table creation and ORM models are managed by memu-py (via ``ddl_mode: "create"``
in its DatabaseConfig), so this server does NOT define its own SQLAlchemy models
or maintain its own engine/session objects.
"""

import os
from urllib.parse import quote


def get_database_url() -> str:
    """
    Get database URL from environment variables.

    Priority: DATABASE_URL > constructed from individual variables

    Returns:
        str: Database connection URL

    Raises:
        RuntimeError: If required environment variables are missing
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Normalize common PostgreSQL DSNs to use the psycopg async driver.
        # Handle bare postgres:// and postgresql:// URLs that don't specify a driver.
        if database_url.startswith("postgres://"):
            # postgres://user:pass@host/db -> postgresql+psycopg://user:pass@host/db
            database_url = "postgresql+psycopg://" + database_url[len("postgres://") :]
        elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
            # postgresql://user:pass@host/db -> postgresql+psycopg://user:pass@host/db
            database_url = "postgresql+psycopg://" + database_url[len("postgresql://") :]

        # Convert asyncpg driver to psycopg if needed (asyncpg is not a project dependency)
        # postgresql+asyncpg:// -> postgresql+psycopg://
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = "postgresql+psycopg://" + database_url[len("postgresql+asyncpg://") :]

        return database_url

    # Construct from individual variables
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT", "5432")  # Default PostgreSQL port
    db_user = os.getenv("DATABASE_USER")
    db_pass = os.getenv("DATABASE_PASSWORD")
    db_name = os.getenv("DATABASE_NAME")

    required_vars: dict[str, str | None] = {
        "DATABASE_HOST": db_host,
        "DATABASE_USER": db_user,
        "DATABASE_PASSWORD": db_pass,
        "DATABASE_NAME": db_name,
    }
    missing_vars = [name for name, value in required_vars.items() if not value]

    if missing_vars:
        msg = f"Database configuration is incomplete. Missing environment variables: {', '.join(missing_vars)}"
        raise RuntimeError(msg)

    # After validation, narrow types for mypy (values are guaranteed non-None and non-empty)
    db_host = str(db_host)
    db_user = str(db_user)
    db_pass = str(db_pass)
    db_name = str(db_name)

    # URL-encode username and password to handle special characters like '@', ':', '/'
    # Use quote(..., safe="") instead of quote_plus() for URL userinfo section
    db_user_encoded = quote(db_user, safe="")
    db_pass_encoded = quote(db_pass, safe="")

    return f"postgresql+psycopg://{db_user_encoded}:{db_pass_encoded}@{db_host}:{db_port}/{db_name}"
