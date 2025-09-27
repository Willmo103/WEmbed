from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class IgnoreExtSchema(BaseModel):
    ext: str


class IgnoreExtTable(Base):
    __tablename__ = "_dl_ignore_ext"
    ext: Mapped[str] = mapped_column(String, primary_key=True, index=True)
