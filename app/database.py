"""Database configuration and session management."""

import os
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


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
        if "+asyncpg" in database_url:
            database_url = database_url.replace("+asyncpg", "+psycopg", 1)

        return database_url

    # Construct from individual variables
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT", "5432")  # Default PostgreSQL port
    db_user = os.getenv("DATABASE_USER")
    db_pass = os.getenv("DATABASE_PASSWORD")
    db_name = os.getenv("DATABASE_NAME")

    # TODO: Improve validation to check for empty strings explicitly
    # Current check 'if not value' treats empty string as missing
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

    # At this point, we know db_user, db_pass, db_host, db_name are not None
    # Use assertion to help mypy understand this
    assert db_user is not None
    assert db_pass is not None
    assert db_host is not None
    assert db_name is not None

    # URL-encode username and password to handle special characters like '@', ':', '/'
    # Use quote(..., safe="") instead of quote_plus() for URL userinfo section
    db_user_encoded = quote(db_user, safe="")
    db_pass_encoded = quote(db_pass, safe="")

    return f"postgresql+psycopg://{db_user_encoded}:{db_pass_encoded}@{db_host}:{db_port}/{db_name}"


# TODO: Consider lazy initialization to avoid executing during module import
# This would prevent database connection issues from failing tests that don't use the database
# Get database URL using the shared function
DATABASE_URL = get_database_url()

# Create SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
# Async session factory
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)
# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for FastAPI to get async database session."""
    async with SessionLocal() as db:
        yield db
