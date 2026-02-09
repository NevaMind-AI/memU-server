"""Memory models for storing and retrieving memories."""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel, Text

from .base import BaseModel


class MemoryBase(SQLModel):
    """Base schema for Memory model."""

    user_id: str = Field(index=True, description="User ID who owns this memory")
    agent_id: str | None = Field(default=None, index=True, description="Agent ID if applicable")
    memory_id: str = Field(index=True, description="External memory ID from memu-py")
    category: str | None = Field(default=None, index=True, description="Memory category name")
    content: str = Field(sa_column=Column(Text, nullable=False), description="Memory content text")
    embedding: list[float] | None = Field(
        default=None, sa_column=Column(Vector(1536)), description="Memory embedding vector (1536 dimensions)"
    )
    links: list[Any] | None = Field(default=None, sa_column=Column(JSONB), description="Related links or references")
    happened_at: datetime | None = Field(default=None, description="When the memory event occurred")


class Memory(BaseModel, MemoryBase, table=True):
    """Memory table for storing user memories.

    Stores memories with vector embeddings for similarity search.
    """

    __tablename__ = "memories"


class MemoryCreate(MemoryBase):
    """Schema for creating a new memory."""

    pass


class MemoryRead(MemoryBase):
    """Schema for reading a memory."""

    id: str
    created_at: datetime
    updated_at: datetime


class MemoryUpdate(SQLModel):
    """Schema for updating a memory."""

    content: str | None = None
    category: str | None = None
    links: list[Any] | None = None
    embedding: list[float] | None = None
    happened_at: datetime | None = None
