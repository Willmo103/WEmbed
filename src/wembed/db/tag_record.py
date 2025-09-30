"""
This module defines the TagRecord, TagSchema, and TagRepo classes for managing tags in the database.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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

    _db_svc: DbService

    def __init__(self, db_svc: DbService):
        self._db_svc = db_svc

    def create(self, value: str, description: Optional[str] = None) -> TagRecordSchema:
        """Creates a new tag in the database."""
        with self._db_svc.get_session()() as session:
            tag = TagRecord(value=value, description=description)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return self.from_schema(tag)

    def update(
        self,
        tag_id: int,
        value: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[TagRecordSchema]:
        """Updates an existing tag in the database."""
        with self._db_svc.get_session()() as session:
            tag = session.get(TagRecord, tag_id)
            if not tag:
                return None
            if value is not None:
                tag.value = value
            if description is not None:
                tag.description = description
            session.commit()
            session.refresh(tag)
            return self.from_schema(tag)

    def delete(self, tag_id: int) -> bool:
        """Deletes a tag from the database."""
        with self._db_svc.get_session()() as session:
            tag = session.get(TagRecord, tag_id)
            if not tag:
                return False
            session.delete(tag)
            session.commit()
            return True

    def map_tag_to_item(
        self, tag_id: int, item_id: str, item_source: str
    ) -> TaggedItemSchema:
        """Maps a tag to an item."""
        with self._db_svc.get_session()() as session:
            tagged_item = TaggedItemsTable(
                tag_id=tag_id, tagged_item_id=item_id, tagged_item_source=item_source
            )
            session.add(tagged_item)
            session.commit()
            session.refresh(tagged_item)
            return TaggedItemSchema(**tagged_item.__dict__)

    def unmap_tag_from_item(self, tag_id: int, item_id: str, item_source: str) -> bool:
        """Unmaps a tag from an item."""
        with self._db_svc.get_session()() as session:
            tagged_item = (
                session.query(TaggedItemsTable)
                .filter_by(
                    tag_id=tag_id,
                    tagged_item_id=item_id,
                    tagged_item_source=item_source,
                )
                .first()
            )
            if not tagged_item:
                return False
            session.delete(tagged_item)
            session.commit()
            return True

    def get_all(self) -> List[TagRecordSchema]:
        """Retrieves all tags from the database."""
        with self._db_svc.get_session()() as session:
            tags = session.query(TagRecord).all()
            return [self.from_schema(tag) for tag in tags]

    def get_by_id(self, tag_id: int) -> Optional[TagRecordSchema]:
        """Retrieves a tag by its ID from the database."""
        with self._db_svc.get_session()() as session:
            tag = session.get(TagRecord, tag_id)
            return self.from_schema(tag) if tag else None

    @staticmethod
    def from_schema(tag: TagRecord) -> TagRecordSchema:
        """Converts a TagRecord ORM object to a TagRecordSchema Pydantic model."""
        return TagRecordSchema(
            id=tag.id,
            value=tag.value,
            description=tag.description,
            created_at=tag.created_at,
        )
