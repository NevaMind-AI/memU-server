"""Alembic migration environment configuration.

Note: Memory-related tables are managed by memu-py (via ``ddl_mode: "create"``).
Alembic is kept here for any future server-specific schema migrations.

Configuration note:
    This env.py reuses the application's ``Settings`` class so that Alembic
    reads the same ``POSTGRES_*`` / ``DATABASE_URL`` environment variables as
    the running server.  ``Settings.DATABASE_URL`` is already normalised to
    ``postgresql+psycopg://`` by the ``assemble_db_url`` validator, which is
    the synchronous driver required by Alembic.
"""

# pylint: disable=no-member
from logging.config import fileConfig

from sqlalchemy import pool

from alembic import context
from config.settings import Settings


def get_sync_database_url() -> str:
    """Return a synchronous database URL for Alembic migrations.

    Delegates to ``Settings`` so that the same ``POSTGRES_*`` /
    ``DATABASE_URL`` environment variables used by the application are
    honoured here as well.  The ``assemble_db_url`` field-validator in
    ``Settings`` already normalises the URL to ``postgresql+psycopg://``.

    Returns:
        Synchronous database connection URL suitable for SQLAlchemy.
    """
    settings = Settings()
    return settings.DATABASE_URL


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None
# NOTE: Alembic's autogenerate relies on `target_metadata` to discover the
# current schema from SQLAlchemy models.  It is intentionally set to None
# because all current tables are managed externally by memu-py (see module
# docstring), so there is no server-specific SQLAlchemy metadata to inspect.
#
# Implications:
#   * `alembic revision --autogenerate` will NOT detect any changes.
#   * Any migrations must use explicit operations (e.g. op.create_table).
#
# When you introduce server-specific tables, define a SQLAlchemy
# MetaData / declarative Base and assign it here, for example:
#     from myapp.models import Base
#     target_metadata = Base.metadata

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
