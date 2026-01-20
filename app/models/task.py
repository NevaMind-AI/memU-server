"""Memorize task models for tracking async memory processing."""

from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, SQLModel

from .base import BaseModel


class TaskStatus(str, Enum):
    """Task status enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class MemorizeTaskBase(SQLModel):
    """Base schema for MemorizeTask model."""
    
    user_id: str = Field(index=True, description="User ID")
    agent_id: str | None = Field(default=None, index=True, description="Agent ID")
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        sa_type=sa.Enum(TaskStatus, native_enum=False, length=50),
        description="Task status"
    )
    content: str = Field(description="Content to memorize")
    category: str | None = Field(default=None, description="Target category")
    result: dict | None = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Task result data"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    finished_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="When task finished"
    )
    task_metadata: dict | None = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Additional task metadata"
    )


class MemorizeTask(BaseModel, MemorizeTaskBase, table=True):
    """Memorize task table for tracking async memory processing."""
    
    __tablename__ = "memorize_tasks"


class MemorizeTaskCreate(MemorizeTaskBase):
    """Schema for creating a new memorize task."""
    pass


class MemorizeTaskRead(MemorizeTaskBase):
    """Schema for reading a memorize task."""
    
    id: str
    created_at: datetime
    updated_at: datetime


class MemorizeTaskUpdate(SQLModel):
    """Schema for updating a memorize task."""
    
    status: TaskStatus | None = None
    result: dict | None = None
    error: str | None = None
    finished_at: datetime | None = None
    task_metadata: dict | None = None