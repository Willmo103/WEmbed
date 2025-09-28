from typing import Optional
from pydantic import BaseModel
from ..base import Base
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class TaggedItemsTable(Base):
    """
    SQLAlchemy model for the 'tagged_items' table.
    Represents the many-to-many relationship between tags and items.
    """

    __tablename__ = "tagged_items"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    tagged_item_id: Mapped[str] = mapped_column(String(50), nullable=False)
    tagged_item_source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TaggedItemSchema(BaseModel):
    id: Optional[int] = None
    tag_id: int
    tagged_item_id: str
    tagged_item_source: str
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration to allow population from ORM objects."""
        from_attributes = True
