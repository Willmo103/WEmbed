from pydantic import BaseModel
from sqlalchemy import Column, String

from ..base import Base
# from ..services import DbService

class MdXrefTable(Base):
    __tablename__ = "_dl_md_xref"
    k = Column(String, primary_key=True, index=True)
    v = Column(String, index=True)


class MdXrefSchema(BaseModel):
    k: str
    v: str


class MdXrefController:
    """
    Controller class for MdXrefTable operations.

    Methods:
    - init_db_tables: Initializes the database tables inserting default values if they do not exist.
    - get_mapping: Retrieves the mapping value for a given key.
    - set_mapping: Sets or updates the mapping value for a given key.
    - delete_mapping: Deletes the mapping for a given key.
    """

    def __init__(self, db_svc: DbService):
        self._db_svc = db_svc
