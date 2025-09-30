"""
This module defines the PSHistoryRecord, PSHistoryRecordSchema, and PSHistoryRecordRepo
classes for managing history records in a database using SQLAlchemy ORM.
"""
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, Session
from sqlalchemy import String, Text
from pydantic import BaseModel

from .base import Base

class PSHistoryRecord(Base):
    """
    Represents a history record in the database.
    """
    __tablename__ = "ps_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    command: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(tz=timezone.utc))
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    host: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class PSHistoryRecordSchema(BaseModel):
    id: Optional[str] = None
    command: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    host: Optional[str] = None
    user: Optional[str] = None

    class Config:
        """Pydantic configuration to allow population from ORM objects."""
        from_attributes = True


class PSHistoryRecordRepo:
    """
    Repository class for PSHistoryRecord entities.
    Provides methods to create, compare, and retrieve history records.

    Methods:
        - create: Create a new history record.
        - batch_create: Create multiple history records in a batch.
        - get_by_host_or_user: Retrieve records filtered by host or user.
        - get_by_time_range: Retrieve records within a specific time range.
        - get_all: Retrieve all history records.
        - to_schema: Convert a PSHistoryRecord to its schema representation.
    """


    @staticmethod
    def create(db: Session, record: PSHistoryRecordSchema) -> PSHistoryRecord:
        """
        Create a new history record in the database.

        Args:
            db (Session): The database session.
            record (PSHistoryRecordSchema): The history record data to create.

        Returns:
            PSHistoryRecord: The created history record.
        """
        db_record = PSHistoryRecord(
            command=record.command,
            start_time=record.start_time,
            end_time=record.end_time,
            duration_seconds=record.duration_seconds,
            host=record.host,
            user=record.user
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def batch_create(db: Session, records: List[PSHistoryRecordSchema]) -> List[PSHistoryRecord]:
        """
        Create multiple history records in a batch operation.

        Args:
            db (Session): The database session.
            records (List[PSHistoryRecordSchema]): List of history record data to create.

        Returns:
            List[PSHistoryRecord]: List of created history records.
        """
        db_records = [PSHistoryRecord(
            command=record.command,
            start_time=record.start_time,
            end_time=record.end_time,
            duration_seconds=record.duration_seconds,
            host=record.host,
            user=record.user
        ) for record in records]
        db.add_all(db_records)
        db.commit()
        db.refresh(db_records)
        return db_records

    @staticmethod
    def get_by_host_or_user(db: Session, host: Optional[str] = None, user: Optional[str] = None) -> List[PSHistoryRecord]:
        """
        Retrieve history records filtered by host or user.

        Args:
            db (Session): The database session.
            host (Optional[str]): The host to filter by.
            user (Optional[str]): The user to filter by.
        Returns:
            List[PSHistoryRecord]: List of matching history records.
        """
        query = db.query(PSHistoryRecord)
        if host:
            query = query.filter(PSHistoryRecord.host == host)
        if user:
            query = query.filter(PSHistoryRecord.user == user)
        return query.all()

    @staticmethod
    def get_by_time_range(db: Session, start: datetime, end: datetime) -> List[PSHistoryRecord]:
        """
        Retrieve history records within a specific time range.

        Args:
            db (Session): The database session.
            start (datetime): The start of the time range.
            end (datetime): The end of the time range.

        Returns:
            List[PSHistoryRecord]: List of matching history records.
        """
        return db.query(PSHistoryRecord).filter(
            PSHistoryRecord.start_time >= start,
            PSHistoryRecord.start_time <= end
        ).all()

    @staticmethod
    def get_all(db: Session) -> List[PSHistoryRecord]:
        """
        Retrieve all history records from the database.

        Args:
            db (Session): The database session.

        Returns:
            List[PSHistoryRecord]: List of all history records.
        """
        return db.query(PSHistoryRecord).all()

    @staticmethod
    def to_schema(record: PSHistoryRecord) -> PSHistoryRecordSchema:
        """
        Convert a PSHistoryRecord to its schema representation.

        Args:
            record (PSHistoryRecord): The history record to convert.

        Returns:
            PSHistoryRecordSchema: The schema representation of the history record.
        """
        return PSHistoryRecordSchema(
            id=record.id,
            command=record.command,
            start_time=record.start_time,
            end_time=record.end_time,
            duration_seconds=record.duration_seconds,
            host=record.host,
            user=record.user
        )
