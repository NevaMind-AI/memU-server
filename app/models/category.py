"""Memory category models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel, Text

from .base import BaseModel

if TYPE_CHECKING:
    from .memory import Memory


class MemoryCategoryBase(SQLModel):
    """Base schema for MemoryCategory model."""
    
    user_id: str = Field(index=True, description="User ID who owns this category")
    agent_id: str | None = Field(default=None, index=True, description="Agent ID if applicable")
    name: str = Field(index=True, description="Category name")
    category_type: str = Field(
        default="auto",
        index=True,
        description="Category type: 'auto' or 'manual'"
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Category description"
    )
    config: dict | None = Field(
        default=None,
        sa_column=Column(JSONB),
        description="Category configuration"
    )
    is_active: bool = Field(default=True, description="Whether category is active")
    memory_count: int = Field(default=0, description="Number of memories in this category")


class MemoryCategory(BaseModel, MemoryCategoryBase, table=True):
    """Memory category table."""
    
    __tablename__ = "memory_categories"
    
    # Optional relationship
    # memories: list["Memory"] = Relationship(back_populates="category_rel")


class MemoryCategoryCreate(MemoryCategoryBase):
    """Schema for creating a new memory category."""
    pass


class MemoryCategoryRead(MemoryCategoryBase):
    """Schema for reading a memory category."""
    
    id: str
    created_at: datetime
    updated_at: datetime


class MemoryCategoryUpdate(SQLModel):
    """Schema for updating a memory category."""
    
    name: str | None = None
    description: str | None = None
    config: dict | None = None
    is_active: bool | None = None
    memory_count: int | None = None