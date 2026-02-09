"""Base model mixin for all database models."""

from datetime import UTC, datetime

from sqlmodel import DateTime, Field, SQLModel
from svix_ksuid import ksuid


class BaseModel(SQLModel):
    """Base model with common fields for all tables.

    Provides auto-generated id and timestamps for all database models.
    """

    id: str = Field(
        default_factory=lambda: str(ksuid()),
        primary_key=True,
        index=True,
        description="Primary key using KSUID",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),  # type: ignore[call-overload]
        description="Last update timestamp",
    )
