from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ...services.db_service import DbService
from ..base import Base


class IgnoreExtSchema(BaseModel):
    ext: str


class IgnoreExtTable(Base):
    __tablename__ = "_dl_ignore_ext"
    ext: Mapped[str] = mapped_column(String, primary_key=True, index=True)


class IgnoreExtController:
    """
    Controller class for IgnoreExtTable operations.

    Methods:
    - add_extension: Adds a new file extension to ignore.
    - get_all_extensions: Retrieves all ignored file extensions.
    - delete_extension: Deletes a specific file extension from ignore list.
    """

    def __init__(self, db_svc: DbService):
        self._db_svc = db_svc

    def create(self, ext: str) -> IgnoreExtSchema:
        """Adds a new file extension to the ignore list in the database."""
        with self._db_svc.get_session()() as session:
            ignore_ext = IgnoreExtTable(ext=ext)
            session.add(ignore_ext)
            session.commit()
            session.refresh(ignore_ext)
            return self.from_schema(ignore_ext)

    def get_all(self) -> list[IgnoreExtSchema]:
        """Retrieves all ignored file extensions from the database."""
        with self._db_svc.get_session()() as session:
            exts = session.query(IgnoreExtTable).all()
            return [self.from_schema(ext) for ext in exts]

    def delete(self, ext: str) -> bool:
        """Deletes a specific file extension from the ignore list in the database."""
        with self._db_svc.get_session()() as session:
            ignore_ext = session.get(IgnoreExtTable, ext)
            if ignore_ext:
                session.delete(ignore_ext)
                session.commit()
                return True
            return False

    def initialize_defaults(self, defaults: list[str]) -> None:
        """Initializes the database with a set of default ignored extensions."""
        with self._db_svc.get_session()() as session:
            for ext in defaults:
                ignore_ext = session.get(IgnoreExtTable, ext)
                if not ignore_ext:
                    ignore_ext = IgnoreExtTable(ext=ext)
                    session.add(ignore_ext)
            session.commit()

    @staticmethod
    def from_schema(ignore_ext: IgnoreExtTable) -> IgnoreExtSchema:
        """Converts an IgnoreExtTable instance to its schema representation."""
        return IgnoreExtSchema(ext=ignore_ext.ext)
