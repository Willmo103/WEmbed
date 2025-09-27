from pydantic import BaseModel
from sqlalchemy import Column, String

from ..base import Base


class IgnorePartsTable(Base):
    __tablename__ = "_dl_ignore_parts"
    part = Column(String, primary_key=True, index=True)


class IgnorePartsSchema(BaseModel):
    part: str
