"""Alembic migration environment configuration."""

import os

# pylint: disable=no-member
from logging.config import fileConfig
from urllib.parse import quote

from sqlalchemy import pool

# Import the models package so any models imported in app.models are
# registered in Base.metadata for Alembic autogenerate.
import app.models  # noqa: F401
from alembic import context

# Import Base metadata for autogenerate support
# Note: We import from app.models.base which is side-effect free
# (doesn't create database connections or read environment variables)
from app.models.base import Base


def get_sync_database_url() -> str:
    """
    Get synchronous database URL for Alembic migrations.

    Alembic uses synchronous database connections, so we need to convert
    the async URL (postgresql+asyncpg://) to sync format (postgresql+psycopg://).

    Returns:
        str: Synchronous database connection URL
    """
    # First try DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Normalize common PostgreSQL DSNs to use the psycopg (sync) driver.
        # Handle bare postgres:// and postgresql:// URLs that don't specify a driver.
        if database_url.startswith("postgres://"):
            # postgres://user:pass@host/db -> postgresql+psycopg://user:pass@host/db
            database_url = "postgresql+psycopg://" + database_url[len("postgres://") :]
        elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
            # postgresql://user:pass@host/db -> postgresql+psycopg://user:pass@host/db
            database_url = "postgresql+psycopg://" + database_url[len("postgresql://") :]

        # Convert async driver to sync driver if needed
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

    # Validate required environment variables (consistent with app/database.py)
    missing_vars = [
        name
        for name, value in [
            ("DATABASE_HOST", db_host),
            ("DATABASE_USER", db_user),
            ("DATABASE_PASSWORD", db_pass),
            ("DATABASE_NAME", db_name),
        ]
        if not value
    ]

    if missing_vars:
        raise RuntimeError(
            f"Database configuration is incomplete. Missing environment variables: {', '.join(missing_vars)}"
        )

    # At this point, we know these are not None
    assert db_host is not None
    assert db_user is not None
    assert db_pass is not None
    assert db_name is not None

    # URL-encode username and password to handle special characters
    # Use quote(..., safe="") instead of quote_plus() for URL userinfo section
    db_user_encoded = quote(db_user, safe="")
    db_pass_encoded = quote(db_pass, safe="")

    # Use psycopg (sync) for Alembic migrations
    return f"postgresql+psycopg://{db_user_encoded}:{db_pass_encoded}@{db_host}:{db_port}/{db_name}"


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get URL from environment variables
    url = get_sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy import create_engine

    # Get URL from environment variables and create engine directly
    url = get_sync_database_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
