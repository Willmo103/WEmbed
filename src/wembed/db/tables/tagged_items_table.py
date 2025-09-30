from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class TaggedItemsTable(Base):
    """
    SQLAlchemy model for the 'tagged_items' table.
    Represents the many-to-many relationship between tags and items.
    """

    __tablename__ = "tagged_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    tagged_item_id: Mapped[str] = mapped_column(String(50), nullable=False)
    tagged_item_source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaggedItemSchema(BaseModel):
    id: Optional[int] = Field(
        None,
        description="Unique identifier for the tagged item AUTO INCREMENT in the database",
    )
    tag_id: int = Field(..., description="PK of the associated tag from the tags table")
    tagged_item_id: str = Field(
        ..., max_length=50, description="PK of the item being tagged"
    )
    tagged_item_source: str = Field(
        ...,
        max_length=50,
        description="Tablename of the source table of the tagged item",
    )
    created_at: Optional[datetime] = Field(
        None, description="Timestamp when the tagged item was created"
    )

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True
