from sqlalchemy import (
    BINARY,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import BYTEA

Base = declarative_base()


class InputModel(Base):
    __tablename__ = "inputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    errors = Column(String, nullable=True)
    added_at = Column(DateTime, nullable=False)
