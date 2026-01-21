"""Database configuration and session management."""

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

# Database URL from environment variables
# Priority: DATABASE_URL > constructed from individual variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_host = os.getenv("DATABASE_HOST")
    db_port = os.getenv("DATABASE_PORT")
    db_user = os.getenv("DATABASE_USER")
    db_pass = os.getenv("DATABASE_PASSWORD")
    db_name = os.getenv("DATABASE_NAME")

    missing_vars = [
        name
        for name, value in [
            ("DATABASE_HOST", db_host),
            ("DATABASE_PORT", db_port),
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

    DATABASE_URL = f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

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
