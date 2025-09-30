from pydantic import BaseModel
from sqlalchemy import Column, String

from ..base import Base
from ...services import DbService

class MdXrefTable(Base):
    __tablename__ = "_dl_md_xref"
    k = Column(String, primary_key=True, index=True)
    v = Column(String, index=True)


class MdXrefSchema(BaseModel):
    k: str
    v: str

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


    def add_mapping(self, k: str, v: str) -> MdXrefSchema:
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

    def set_mapping(self, k: str, v: str) -> MdXrefSchema:
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

    def delete_mapping(self, k: str) -> bool:
        """Deletes the mapping for a given key."""
        with self._db_svc.get_session()() as session:
            mapping = session.get(MdXrefTable, k)
            if mapping:
                session.delete(mapping)
                session.commit()
                return True
            return False

    @staticmethod
    def from_schema(mapping: MdXrefTable) -> MdXrefSchema:
        """Converts a MdXrefTable instance to its schema representation."""
        return MdXrefSchema(k=mapping.k, v=mapping.v)

