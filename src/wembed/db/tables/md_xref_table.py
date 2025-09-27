from pydantic import BaseModel
from sqlalchemy import Column, String

from ..base import Base


class MdXrefTable(Base):
    __tablename__ = "_dl_md_xref"
    k = Column(String, primary_key=True, index=True)
    v = Column(String, index=True)


class MdXrefSchema(BaseModel):
    k: str
    v: str
