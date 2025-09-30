from pydantic import BaseModel, Field
from sqlalchemy import Column, String

from ...services import DbService
from ..base import Base


class MdXrefTable(Base):
    __tablename__ = "_dl_md_xref"
    k = Column(String, primary_key=True, index=True)
    v = Column(String, index=True)


class MdXrefSchema(BaseModel):
    k: str = Field(
        ..., max_length=100, description="The file extension of the file content type."
    )
    v: str = Field(
        ...,
        max_length=100,
        description="The markdown codeblock language to use for this file type.",
    )

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True


class MdXrefController:
    """
    Controller class for MdXrefTable operations.

    Methods:
    - add_mapping: Adds a new key-value mapping.
    - get_mapping: Retrieves the mapping value for a given key.
    - set_mapping: Sets or updates the mapping value for a given key.
    - delete_mapping: Deletes the mapping for a given key.
    """

    def __init__(self, db_svc: DbService):
        self._db_svc = db_svc

    def create(self, k: str, v: str) -> MdXrefSchema:
        """Adds a new key-value mapping to the database."""
        with self._db_svc.get_session()() as session:
            mapping = MdXrefTable(k=k, v=v)
            session.add(mapping)
            session.commit()
            session.refresh(mapping)
            return self.from_schema(mapping)

    def get_mapping(self, k: str) -> str:
        """Retrieves the mapping value for a given key."""
        with self._db_svc.get_session()() as session:
            mapping = session.get(MdXrefTable, k)
            if mapping:
                return mapping.v
            return "plaintext"

    def update(self, k: str, v: str) -> MdXrefSchema:
        """Sets or updates the mapping value for a given key."""
        with self._db_svc.get_session()() as session:
            mapping = session.get(MdXrefTable, k)
            if mapping:
                mapping.v = v
            else:
                mapping = MdXrefTable(k=k, v=v)
                session.add(mapping)
            session.commit()
            session.refresh(mapping)
            return self.from_schema(mapping)

    def delete(self, k: str) -> bool:
        """Deletes the mapping for a given key."""
        with self._db_svc.get_session()() as session:
            mapping = session.get(MdXrefTable, k)
            if mapping:
                session.delete(mapping)
                session.commit()
                return True
            return False

    def initialize_defaults(self, defaults: dict[str, str]) -> None:
        """Initializes the database with a set of default key-value mappings."""
        with self._db_svc.get_session()() as session:
            for k, v in defaults.items():
                mapping = session.get(MdXrefTable, k)
                if not mapping:
                    mapping = MdXrefTable(k=k, v=v)
                    session.add(mapping)
            session.commit()

    @staticmethod
    def from_schema(mapping: MdXrefTable) -> MdXrefSchema:
        """Converts a MdXrefTable instance to its schema representation."""
        return MdXrefSchema(k=mapping.k, v=mapping.v)
