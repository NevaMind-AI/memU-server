"""Base model mixin for all database models."""

from datetime import UTC, datetime

from ksuid import ksuid
from sqlmodel import DateTime, Field, SQLModel


class BaseModel(SQLModel):
    """Base model with common fields for all tables.

    Provides auto-generated id and timestamps for all database models.
    """

    id: str = Field(
        default_factory=lambda: str(ksuid()),
        primary_key=True,
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
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
        description="Last update timestamp",
    )


# Alias used by Alembic ('Base.metadata') for autogenerate
Base = SQLModel
