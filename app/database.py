"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

import os

# Database URL from environment variables
# Priority: DATABASE_URL > constructed from individual variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "54320")
    db_user = os.getenv("DATABASE_USER", "memu_user")
    db_pass = os.getenv("DATABASE_PASSWORD", "memu_pass")
    db_name = os.getenv("DATABASE_NAME", "memu_db")
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
