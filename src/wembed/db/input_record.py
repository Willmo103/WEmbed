"""
(File: src/wembed/db/input_record.py)
SQLAlchemy models and Pydantic schemas for input records, along with Repository classes for CRUD operations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class InputRecord(Base):
    """
    SQLAlchemy model for input records.
    Attributes:
    - id (int): Unique identifier for the input record.
    - source_type (str): Type of the input source (e.g., 'file', 'url').
    - status (str): Current status of the input (e.g., 'pending', 'processed', 'error').
    - errors (Optional[str]): Any error messages associated with the input.
    - added_at (datetime): Timestamp when the input was added.
    - processed (bool): Flag indicating if the input has been processed.
    - processed_at (Optional[datetime]): Timestamp when the input was processed.
    - output_doc_id (Optional[int]): Foreign key linking to the output document record.
    - input_file_id (Optional[str]): Foreign key linking to the associated file record.
    """

    __tablename__ = "dl_inputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    output_doc_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dl_documents.id"), nullable=True
    )
    input_file_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("dl_files.id"), nullable=True
    )


class InputRecordSchema(BaseModel):
    id: Optional[int] = None
    source_type: str
    status: str
    errors: Optional[List[str]] = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processed_at: Optional[datetime] = None
    output_doc_id: Optional[int] = None
    input_file_id: Optional[str] = None

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True


class InputOut(BaseModel):
    id: int
    source: str
    source_type: str
    status: str
    errors: Optional[List[str]] = None
    files: Optional[List[str]] = None
    added_at: datetime
    processed_at: Optional[datetime] = None
    total_files: int = 0

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True


class InputRecordRepo:
    """Repository class for InputRecord entities
    Provides CRUD operations for InputRecord.

    Methods:
    - create: Create a new input record.
    - get_by_id: Retrieve an input record by its ID.
    - get_by_source_type: Retrieve input records by source type.
    - get_by_status: Retrieve input records by status.
    - get_unprocessed: Retrieve unprocessed input records.
    - get_by_file_id: Retrieve an input record by associated file ID.
    - get_all: Retrieve all input records with pagination.
    - update: Update an existing input record.
    - mark_processed: Mark an input record as processed.
    - add_error: Add an error message to an input record.
    - delete: Delete an input record by its ID.
    - to_schema: Convert an InputRecord to InputRecordSchema.
    """

    @staticmethod
    def create(db: Session, input_record: InputRecordSchema) -> InputRecord:
        """
        Create a new input record in the database.

        Args:
            db: Database session
            input_record: Input record data to be added

        Returns:
            InputRecord: The created InputRecord object.
        """
        db_record = InputRecord(
            source_type=input_record.source_type,
            status=input_record.status,
            errors=("\n".join(input_record.errors) if input_record.errors else None),
            added_at=input_record.added_at,
            processed=input_record.processed,
            processed_at=input_record.processed_at,
            output_doc_id=input_record.output_doc_id,
            input_file_id=input_record.input_file_id,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, input_id: int) -> Optional[InputRecord]:
        """
        Retrieve an input record by its ID.

        Args:
            db: Database session
            input_id: ID of the input record to retrieve

        Returns:
            Optional[InputRecord]: The retrieved InputRecord object or None if not found.
        """
        return db.query(InputRecord).filter(InputRecord.id == input_id).first()

    @staticmethod
    def get_by_source_type(db: Session, source_type: str) -> List[InputRecordSchema]:
        """
        Retrieve input records by source type.

        Args:
            db: Database session
            source_type: Source type to filter input records

        Returns:
            List[InputRecord]: List of InputRecord objects matching the source type.
        """
        results = (
            db.query(InputRecord).filter(InputRecord.source_type == source_type).all()
        )
        try:
            return [InputRecordSchema(**r.__dict__) for r in results]
        except Exception as e:
            db.rollback()
            return []

    @staticmethod
    def get_by_status(db: Session, status: str) -> List[InputRecordSchema]:
        """
        Retrieve input records by status.

        Args:
            db: Database session
            status: Status to filter input records

        Returns:
            List[InputRecordSchema]: List of InputRecordSchema objects matching the status.
        """

        results = db.query(InputRecord).filter(InputRecord.status == status).all()
        try:
            return [InputRecordSchema(**r.__dict__) for r in results]
        except Exception:
            return []

    @staticmethod
    def get_unprocessed(db: Session) -> List[InputRecordSchema]:
        """
        Retrieve unprocessed input records.

        Args:
            db: Database session
            status: Status to filter input records

        Returns:
            List[InputRecord]: List of InputRecord objects matching the status.
        """
        results = db.query(InputRecord).filter(InputRecord.processed == False).all()
        try:
            return [InputRecordSchema(**r.__dict__) for r in results]
        except Exception as e:
            db.rollback()
            return []

    @staticmethod
    def get_by_file_id(db: Session, file_id: str) -> Optional[InputRecord]:
        """
        Retrieve an input record by associated file ID.

        Args:
            db: Database session
            file_id: ID of the associated file

        Returns:
            Optional[InputRecord]: The retrieved InputRecord object or None if not found.
        """
        return (
            db.query(InputRecord).filter(InputRecord.input_file_id == file_id).first()
        )

    @staticmethod
    def get_all(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[InputRecordSchema]:
        """
        Retrieve all input records with pagination.

        Args:
            db: Database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List[InputRecordSchema]: List of InputRecordSchema objects.
        """
        results = db.query(InputRecord).offset(skip).limit(limit).all()
        try:
            records = [InputRecord(**r.__dict__) for r in results]
            return [InputRecordSchema(**r.__dict__) for r in records]
        except Exception as e:
            db.rollback()
            return []

    @staticmethod
    def update(
        db: Session, input_id: int, input_record: InputRecordSchema
    ) -> Optional[InputRecord]:
        """
        Update an existing input record.

        Args:
            db: Database session
            input_id: ID of the input record to update
            input_record: InputRecordSchema object containing the updated data

        Returns:
            Optional[InputRecord]: The updated InputRecord object or None if not found.
        """
        db_record = InputRecordRepo.get_by_id(db, input_id)
        if db_record:
            update_data = input_record.model_dump(exclude_unset=True, exclude={"id"})
            if "errors" in update_data and update_data["errors"]:
                update_data["errors"] = "\n".join(update_data["errors"])

            for key, value in update_data.items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def mark_processed(
        db: Session, input_id: int, output_doc_id: Optional[int] = None
    ) -> Optional[InputRecord]:
        """
        Mark an input record as processed.

        Args:
            db: Database session
            input_id: ID of the input record to mark as processed
            output_doc_id: Optional ID of the associated output document

        Returns:
            Optional[InputRecord]: The updated InputRecord object or None if not found.
        """
        db_record = InputRecordRepo.get_by_id(db, input_id)
        if db_record:
            db_record.processed = True
            db_record.processed_at = datetime.now(timezone.utc)
            db_record.status = "processed"
            if output_doc_id:
                db_record.output_doc_id = output_doc_id
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def add_error(db: Session, input_id: int, error: str) -> Optional[InputRecord]:
        """
        Add an error message to an input record and update its status to 'error'.

        Args:
            db: Database session
            input_id: ID of the input record to update
            error: Error message to add

        Returns:
            Optional[InputRecord]: The updated InputRecord object or None if not found.
        """
        db_record = InputRecordRepo.get_by_id(db, input_id)
        if db_record:
            existing_errors = db_record.errors.split("\n") if db_record.errors else []
            existing_errors.append(error)
            db_record.errors = "\n".join(existing_errors)
            db_record.status = "error"
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, input_id: int) -> bool:
        """
        Delete an input record by its ID.

        Args:
            db: Database session
            input_id: ID of the input record to delete

        Returns:
            bool: True if the record was deleted, False if not found.
        """
        db_record = InputRecordRepo.get_by_id(db, input_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: InputRecord) -> InputRecordSchema:
        """
        Convert an InputRecord to InputRecordSchema.

        Args:
            record: InputRecord object to convert

        Returns:
            InputRecordSchema: The corresponding InputRecordSchema object.
        """
        return InputRecordSchema(
            id=record.id,
            source_type=record.source_type,
            status=record.status,
            errors=record.errors.split("\n") if record.errors else None,
            added_at=record.added_at,
            processed=record.processed,
            processed_at=record.processed_at,
            output_doc_id=record.output_doc_id,
            input_file_id=record.input_file_id,
        )
