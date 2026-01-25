"""Database configuration and session management."""

import logging
import os
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)


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
        return database_url
    
    # Construct from individual variables
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT", "54320")  # Default PostgreSQL port
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

    # URL-encode username and password to handle special characters like '@', ':', '/'
    db_user_encoded = quote_plus(db_user)
    db_pass_encoded = quote_plus(db_pass)
    
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
