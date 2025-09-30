"""
Database models, schemas and repository operations for document indexing.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class DocumentIndexRecord(Base):
    """
    SQLAlchemy model for document indices.
    Attributes:
    - id (int): Unique identifier for the document index.
    - file_id (str): Foreign key linking to the associated file record.
    - last_rendered (Optional[datetime]): Timestamp of the last rendering operation.
    """

    __tablename__ = "dl_document_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("dl_files.id"), nullable=False)
    last_rendered: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DocumentIndexSchema(BaseModel):
    id: Optional[int] = None
    file_id: str
    last_rendered: Optional[datetime] = None

    class Config:
        """Pydantic configuration to allow population from ORM objects."""

        from_attributes = True


class DocumentIndexRepo:
    """Repository class for DocumentIndexRecord entities"""

    @staticmethod
    def create(db: Session, doc_index: DocumentIndexSchema) -> DocumentIndexRecord:
        """
        Create a new document index record in the database.

        Args:
            db (Session): The database session.
            doc_index (DocumentIndexSchema): The document index data to create.

        Returns:
            DocumentIndexRecord: The created document index record.
        """
        db_record = DocumentIndexRecord(
            file_id=doc_index.file_id, last_rendered=doc_index.last_rendered
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, doc_index_id: int) -> Optional[DocumentIndexRecord]:
        """
        Retrieve a document index by its ID.

        Args:
            db (Session): The database session.
            doc_index_id (int): The ID of the document index to retrieve.

        Returns:
            Optional[DocumentIndexRecord]: The document index record if found, else None.
        """
        return (
            db.query(DocumentIndexRecord)
            .filter(DocumentIndexRecord.id == doc_index_id)
            .first()
        )

    @staticmethod
    def get_by_file_id(db: Session, file_id: str) -> Optional[DocumentIndexRecord]:
        """
        Retrieve a document index by its associated file ID.

        Args:
            db (Session): The database session.
            file_id (str): The ID of the file whose document index to retrieve.

        Returns:
            Optional[DocumentIndexRecord]: The document index record if found, else None.
        """
        return (
            db.query(DocumentIndexRecord)
            .filter(DocumentIndexRecord.file_id == file_id)
            .first()
        )

    @staticmethod
    def get_all(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[DocumentIndexSchema]:
        """
        Fetch all document indices with pagination.

        Args:
            db (Session): The database session.
            skip (int): Number of records to skip for pagination.
            limit (int): Maximum number of records to return.

        Returns:
            list[DocumentIndexSchema]: A list of document index schemas.
        """
        _records = db.query(DocumentIndexRecord).offset(skip).limit(limit).all()
        try:
            records = [DocumentIndexRecord(**r.__dict__) for r in _records]
            return [DocumentIndexRepo.to_schema(rec) for rec in records]
        except Exception:
            return []

    @staticmethod
    def get_unrendered(db: Session) -> list[DocumentIndexSchema]:
        """
        Fetch all document indices that have not been rendered yet (i.e., last_rendered is None).

        Args:
            db (Session): The database session.

        Returns:
            list[DocumentIndexSchema]: A list of unrendered document index schemas.
        """
        results = (
            db.query(DocumentIndexRecord)
            .filter(DocumentIndexRecord.last_rendered is None)
            .all()
        )
        try:
            records = [DocumentIndexRecord(**r.__dict__) for r in results]
            return [DocumentIndexRepo.to_schema(rec) for rec in records]
        except Exception:
            return []

    @staticmethod
    def update(
        db: Session, doc_index_id: int, doc_index: DocumentIndexSchema
    ) -> Optional[DocumentIndexRecord]:
        """
        Update a document index by its ID.

        Args:
            db (Session): The database session.
            doc_index_id (int): The ID of the document index to update.
            doc_index (DocumentIndexSchema): The updated document index data.

        Returns:
            Optional[DocumentIndexRecord]: The updated document index record, or None if not found.
        """
        db_record = DocumentIndexRepo.get_by_id(db, doc_index_id)
        if db_record:
            for key, value in doc_index.model_dump(
                exclude_unset=True, exclude={"id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_last_rendered(
        db: Session, file_id: str, rendered_time: Optional[datetime] = None
    ) -> Optional[DocumentIndexRecord]:
        """
        Update the last_rendered timestamp of a document index by its associated file ID.

        Args:
            db (Session): The database session.
            file_id (str): The ID of the file whose document index to update.
            rendered_time (Optional[datetime]): The new timestamp to set. If None, uses current UTC time.

        Returns:
            Optional[DocumentIndexRecord]: The updated document index record, or None if not found.
        """
        db_record = DocumentIndexRepo.get_by_file_id(db, file_id)
        if db_record:
            db_record.last_rendered = rendered_time or datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, doc_index_id: int) -> bool:
        """
        Delete a document index by its ID.

        Args:
            db (Session): The database session.
            doc_index_id (int): The ID of the document index to delete.

        Returns:
            bool: True if the record was deleted, False if not found.
        """
        db_record = DocumentIndexRepo.get_by_id(db, doc_index_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_by_file_id(db: Session, file_id: str) -> bool:
        """
        Delete a document index by its associated file ID.

        Args:
            db (Session): The database session.
            file_id (str): The ID of the file whose document index to delete.

        Returns:
            bool: True if the record was deleted, False if not found.
        """
        db_record = DocumentIndexRepo.get_by_file_id(db, file_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: DocumentIndexRecord) -> DocumentIndexSchema:
        """
        Convert a DocumentIndexRecord to a DocumentIndexSchema.

        Args:
            record (DocumentIndexRecord): The database record to convert.

        Returns:
            DocumentIndexSchema: The corresponding Pydantic schema.
        """
        return DocumentIndexSchema(
            id=record.id,
            file_id=record.file_id,
            last_rendered=record.last_rendered,
        )
