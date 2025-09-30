from pydantic import BaseModel, Field
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ...services import DbService
from ..base import Base


class IgnorePartsTable(Base):
    __tablename__ = "_dl_ignore_parts"
    part: Mapped[str] = mapped_column(String, primary_key=True, index=True)


class IgnorePartsSchema(BaseModel):
    part: str = Field(..., max_length=100)

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True


class IgnorePartsController:
    """
    Controller class for IgnorePartsTable operations.

    Methods:
    - add_part: Adds a new part to ignore.
    - get_all_parts: Retrieves all ignored parts.
    - delete_part: Deletes a specific part from ignore list.
    """
    _db_svc: DbService

    def __init__(self, db_svc: DbService):
        self._db_svc = db_svc

    def create(self, part: str) -> IgnorePartsSchema:
        """Adds a new part to the ignore list in the database."""
        with self._db_svc.get_session()() as session:
            ignore_part = IgnorePartsTable(part=part)
            session.add(ignore_part)
            session.commit()
            session.refresh(ignore_part)
            return self.from_schema(ignore_part)

    def get_all(self) -> list[IgnorePartsSchema]:
        """Retrieves all ignored parts from the database."""
        with self._db_svc.get_session()() as session:
            parts = session.query(IgnorePartsTable).all()
            return [self.from_schema(part) for part in parts]

    def delete(self, part: str) -> bool:
        """Deletes a specific part from the ignore list in the database."""
        with self._db_svc.get_session()() as session:
            ignore_part = session.get(IgnorePartsTable, part)
            if ignore_part:
                session.delete(ignore_part)
                session.commit()
                return True
            return False

    def initialize_defaults(self, defaults: list[str]) -> None:
        """Initializes the database with a set of default ignored parts."""
        with self._db_svc.get_session()() as session:
            for part in defaults:
                ignore_part = session.get(IgnorePartsTable, part)
                if not ignore_part:
                    ignore_part = IgnorePartsTable(part=part)
                    session.add(ignore_part)
            session.commit()

    @staticmethod
    def from_schema(part: IgnorePartsTable) -> IgnorePartsSchema:
        """Converts an IgnorePartsTable instance to its schema representation."""
        return IgnorePartsSchema.from_orm(part)
