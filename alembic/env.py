"""Alembic migration environment configuration."""

import os

# pylint: disable=no-member
from logging.config import fileConfig
from urllib.parse import quote_plus

from sqlalchemy import pool

from alembic import context


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
        # Convert async driver to sync driver if needed
        # postgresql+asyncpg:// -> postgresql+psycopg://
        if "+asyncpg" in database_url:
            database_url = database_url.replace("+asyncpg", "+psycopg")
        return database_url

    # Construct from individual variables
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_user = os.getenv("DATABASE_USER", "postgres")
    db_pass = os.getenv("DATABASE_PASSWORD", "postgres")
    db_name = os.getenv("DATABASE_NAME", "memu")

    # URL-encode username and password to handle special characters
    db_user_encoded = quote_plus(db_user)
    db_pass_encoded = quote_plus(db_pass)

    # Use psycopg (sync) for Alembic migrations
    return f"postgresql+psycopg://{db_user_encoded}:{db_pass_encoded}@{db_host}:{db_port}/{db_name}"


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Note: Import models in env.py only when needed to avoid side effects
#
# TODO: Import your SQLAlchemy Base metadata here for autogenerate support.
# Since this PR adds database.py with a Base class, you should import it:
#
#   from app.database import Base
#   target_metadata = Base.metadata
#
# Without this, Alembic cannot auto-generate migrations from your models.
target_metadata = None

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
