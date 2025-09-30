"""
This module defines the TagRecord, TagSchema, and TagRepo classes for managing tags in the database.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from . import DbService
from .base import Base
from .tables.tagged_items_table import TaggedItemSchema, TaggedItemsTable


class TagRecord(Base):
    """
    SQLAlchemy model for the 'tags' table.
    Represents a tag with its attributes and relationships.
    """

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TagRecordSchema(BaseModel):
    id: Optional[int] = None
    value: str = Field(..., max_length=100)
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True


class TagRecordRepo:
    """
    Repository class for TagRecord entities.
    Provides methods to create, update, delete, map, and unmap tags to other items.
    """

    _db_svc: Optional[DbService]
