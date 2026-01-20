"""Base model mixin for all database models."""

from datetime import datetime, timezone

import ksuid
from sqlmodel import DateTime, Field, SQLModel


class BaseModel(SQLModel):
    """Base model with common fields for all tables."""
    
    id: str = Field(
        default_factory=lambda: str(ksuid.Ksuid()),
        primary_key=True,
        index=True,
        description="Primary key using KSUID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        description="Last update timestamp"
    )