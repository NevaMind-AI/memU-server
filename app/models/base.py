"""SQLAlchemy Base class for model definitions.

This module is intentionally side-effect-free - it only defines the Base class
without creating any database connections or reading environment variables.
This allows safe imports from alembic/env.py for migration autogeneration.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass
