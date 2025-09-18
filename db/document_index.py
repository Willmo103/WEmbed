from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, Session, mapped_column

from ._base import Base


class DocumentIndexRecord(Base):
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
        from_attributes = True


class DocumentIndexCRUD:
    @staticmethod
    def create(db: Session, doc_index: DocumentIndexSchema) -> DocumentIndexRecord:
        db_record = DocumentIndexRecord(
            file_id=doc_index.file_id, last_rendered=doc_index.last_rendered
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, doc_index_id: int) -> Optional[DocumentIndexRecord]:
        return (
            db.query(DocumentIndexRecord)
            .filter(DocumentIndexRecord.id == doc_index_id)
            .first()
        )

    @staticmethod
    def get_by_file_id(db: Session, file_id: str) -> Optional[DocumentIndexRecord]:
        return (
            db.query(DocumentIndexRecord)
            .filter(DocumentIndexRecord.file_id == file_id)
            .first()
        )

    @staticmethod
    def get_all(
        db: Session, skip: int = 0, limit: int = 100
    ) -> list[DocumentIndexRecord]:
        return db.query(DocumentIndexRecord).offset(skip).limit(limit).all()

    @staticmethod
    def get_unrendered(db: Session) -> list[DocumentIndexRecord]:
        return (
            db.query(DocumentIndexRecord)
            .filter(DocumentIndexRecord.last_rendered.is_(None))
            .all()
        )

    @staticmethod
    def update(
        db: Session, doc_index_id: int, doc_index: DocumentIndexSchema
    ) -> Optional[DocumentIndexRecord]:
        db_record = DocumentIndexCRUD.get_by_id(db, doc_index_id)
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
        db_record = DocumentIndexCRUD.get_by_file_id(db, file_id)
        if db_record:
            db_record.last_rendered = rendered_time or datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, doc_index_id: int) -> bool:
        db_record = DocumentIndexCRUD.get_by_id(db, doc_index_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_by_file_id(db: Session, file_id: str) -> bool:
        db_record = DocumentIndexCRUD.get_by_file_id(db, file_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: DocumentIndexRecord) -> DocumentIndexSchema:
        return DocumentIndexSchema(
            id=record.id,
            file_id=record.file_id,
            last_rendered=record.last_rendered,
        )
