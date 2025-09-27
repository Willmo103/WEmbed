from datetime import datetime, timezone
from typing import List, Optional

from docling_core.transforms.chunker.base import BaseChunk
from docling_core.types.doc.document import DoclingDocument
from pydantic import BaseModel, Field, Json
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class DocumentRecord(Base):
    """
    SQLAlchemy model for documents.
    Attributes:
    - id (int): Unique identifier for the document.
    - source (str): The source of the document (e.g., file path, URL).
    - source_type (str): The type of the source (e.g., 'file', 'url').
    - source_ref (Optional[int]): Reference ID to another related entity (e.g., input ID).
    - dl_doc (Optional[str]): The original document content in string format.
    - markdown (Optional[str]): The document content in markdown format.
    - html (Optional[str]): The document content in HTML format.
    - text (Optional[str]): The plain text content of the document.
    - doctags (Optional[str]): Any tags associated with the document.
    - chunks_json (Optional[List[BaseChunk]]): List of chunks derived from the document.
    - created_at (datetime): Timestamp when the document was created.
    - updated_at (Optional[datetime]): Timestamp when the document was last updated.
    """

    __tablename__ = "dl_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_ref: Mapped[Optional[int]] = mapped_column(
        ForeignKey("dl_inputs.id"), nullable=True
    )
    dl_doc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doctags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunks_json: Mapped[Optional[List[BaseChunk]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DocumentRecordSchema(BaseModel):
    id: Optional[int] = None
    source: str
    source_type: str
    source_ref: Optional[int] = None
    dl_doc: Optional[Json[DoclingDocument] | str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    doctags: Optional[str] = None
    chunks_json: Optional[Json[List[BaseChunk]]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    class Config:
        """Configure Pydantic to work with ORM objects."""

        from_attributes = True


class ChunkModel(BaseModel):
    index: int
    chunk: Json[BaseChunk]
    embedding: List[float]

    class Config:
        """Configure Pydantic to work with ORM objects."""

        from_attributes = True


class ChunkList(BaseModel):
    chunks: List[ChunkModel]

    class Config:
        """Configure Pydantic to work with ORM objects."""

        from_attributes = True


class DocumentOut(BaseModel):
    id: int
    source: str
    source_type: str
    source_ref: Optional[str] = None
    dl_doc: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    doctags: Optional[str] = None
    chunks: Optional[ChunkList] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        """Configure Pydantic to work with ORM objects."""

        from_attributes = True


class StringContentOut(BaseModel):
    source: str
    source_type: str
    source_ref: Optional[str] = None
    created_at: str
    content: Optional[str] = None

    class Config:
        """Configure Pydantic to work with ORM objects."""

        from_attributes = True


class DocumentRecordRepo:
    @staticmethod
    def create(db: Session, document: DocumentRecordSchema) -> DocumentRecord:
        db_record = DocumentRecord(
            source=document.source,
            source_type=document.source_type,
            source_ref=document.source_ref,
            dl_doc=str(document.dl_doc) if document.dl_doc else None,
            markdown=document.markdown,
            html=document.html,
            text=document.text,
            doctags=document.doctags,
            chunks_json=document.chunks_json,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, doc_id: int) -> Optional[DocumentRecord]:
        return db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()

    @staticmethod
    def get_by_source(db: Session, source: str) -> Optional[DocumentRecord]:
        return db.query(DocumentRecord).filter(DocumentRecord.source == source).first()

    @staticmethod
    def get_by_source_type(db: Session, source_type: str) -> List[DocumentRecordSchema]:
        results = (
            db.query(DocumentRecord)
            .filter(DocumentRecord.source_type == source_type)
            .all()
        )
        try:
            records = [DocumentRecord(**r.__dict__) for r in results]
            return [DocumentRecordRepo.to_schema(record) for record in records]
        except Exception:
            return []

    @staticmethod
    def get_by_source_ref(db: Session, source_ref: int) -> Optional[DocumentRecord]:
        return (
            db.query(DocumentRecord)
            .filter(DocumentRecord.source_ref == source_ref)
            .first()
        )

    @staticmethod
    def search_by_text(db: Session, search_text: str) -> List[DocumentRecordSchema]:
        results = (
            db.query(DocumentRecord)
            .filter(DocumentRecord.text.contains(search_text))
            .all()
        )
        try:
            records = [DocumentRecord(**r.__dict__) for r in results]
            return [DocumentRecordRepo.to_schema(record) for record in records]
        except Exception:
            return []

    @staticmethod
    def search_by_markdown(db: Session, search_text: str) -> List[DocumentRecordSchema]:
        results = (
            db.query(DocumentRecord)
            .filter(DocumentRecord.markdown.contains(search_text))
            .all()
        )
        try:
            records = [DocumentRecord(**r.__dict__) for r in results]
            return [DocumentRecordRepo.to_schema(record) for record in records]
        except Exception:
            return []

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[DocumentRecord]:
        return db.query(DocumentRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, doc_id: int, document: DocumentRecordSchema
    ) -> Optional[DocumentRecord]:
        db_record = DocumentRecordRepo.get_by_id(db, doc_id)
        if db_record:
            update_data = document.model_dump(exclude_unset=True, exclude={"id"})
            if "dl_doc" in update_data and update_data["dl_doc"]:
                update_data["dl_doc"] = str(update_data["dl_doc"])

            for key, value in update_data.items():
                setattr(db_record, key, value)

            db_record.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_text_content(
        db: Session,
        doc_id: int,
        text: str,
        markdown: Optional[str] = None,
        html: Optional[str] = None,
    ) -> Optional[DocumentRecord]:
        """
        Update the text content of the document by itsID.

        Args:
            db (Session): The database session.
            doc_id (int): The ID of the document to update.
            text (str): The new text content.
            markdown (Optional[str]): The new markdown content, if any.
            html (Optional[str]): The new HTML content, if any.
        Returns:
            Optional[DocumentRecord]: The updated document record, or None if not found.
        """
        db_record = DocumentRecordRepo.get_by_id(db, doc_id)
        if db_record:
            db_record.text = text
            if markdown is not None:
                db_record.markdown = markdown
            if html is not None:
                db_record.html = html
            db_record.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_chunks(
        db: Session, doc_id: int, chunks_json: str
    ) -> Optional[DocumentRecord]:
        """
        Update the chunks_json field of a document by its ID.

        Args:
            db (Session): The database session.
            doc_id (int): The ID of the document to update.
            chunks_json (str): The new chunks JSON data.

        Returns:
            Optional[DocumentRecord]: The updated document record, or None if not found.
        """
        db_record = DocumentRecordRepo.get_by_id(db, doc_id)
        if db_record:
            db_record.chunks_json = chunks_json
            db_record.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, doc_id: int) -> bool:
        """
        Delete a document by its ID.

        Args:
            db (Session): The database session.
            doc_id (int): The ID of the document to delete.

        Returns:
            bool: True if the record was deleted, False if not found.
        """
        db_record = DocumentRecordRepo.get_by_id(db, doc_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: DocumentRecord) -> DocumentRecordSchema:
        """
        Convert a DocumentRecord to a DocumentRecordSchema.

        Args:
            record (DocumentRecord): The database record to convert.

        Returns:
            DocumentRecordSchema: A pydantic schema representation of the record.
        """
        return DocumentRecordSchema(
            id=record.id,
            source=record.source,
            source_type=record.source_type,
            source_ref=record.source_ref,
            dl_doc=record.dl_doc,
            markdown=record.markdown,
            html=record.html,
            text=record.text,
            doctags=record.doctags,
            chunks_json=record.chunks_json,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_document_out(record: DocumentRecord) -> DocumentOut:
        """
        Convert a DocumentRecord to a DocumentOut schema.

        Args:
            record (DocumentRecord): The database record to convert.

        Returns:
            DocumentOut: A pydantic schema representation of the record.
        """
        return DocumentOut(
            id=record.id,
            source=record.source,
            source_type=record.source_type,
            source_ref=str(record.source_ref) if record.source_ref else None,
            dl_doc=record.dl_doc,
            markdown=record.markdown,
            html=record.html,
            text=record.text,
            doctags=record.doctags,
            chunks=None,  # This would need to be populated separately if needed
            created_at=record.created_at.isoformat(),
            updated_at=(record.updated_at.isoformat() if record.updated_at else None),
        )
