from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, Session
from pydantic import BaseModel, Field
from ._base import Base


class InputRecord(Base):
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
        from_attributes = True


class InputRecordCRUD:
    @staticmethod
    def create(db: Session, input_record: InputRecordSchema) -> InputRecord:
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
        return db.query(InputRecord).filter(InputRecord.id == input_id).first()

    @staticmethod
    def get_by_source_type(db: Session, source_type: str) -> List[InputRecord]:
        return (
            db.query(InputRecord).filter(InputRecord.source_type == source_type).all()
        )

    @staticmethod
    def get_by_status(db: Session, status: str) -> List[InputRecord]:
        return db.query(InputRecord).filter(InputRecord.status == status).all()

    @staticmethod
    def get_unprocessed(db: Session) -> List[InputRecord]:
        return (
            db.query(InputRecord)
            .filter(InputRecord.status == "pending")
            .filter(InputRecord.processed == 0)
            .all()
        )

    @staticmethod
    def get_by_file_id(db: Session, file_id: str) -> Optional[InputRecord]:
        return (
            db.query(InputRecord).filter(InputRecord.input_file_id == file_id).first()
        )

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[InputRecord]:
        return db.query(InputRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, input_id: int, input_record: InputRecordSchema
    ) -> Optional[InputRecord]:
        db_record = InputRecordCRUD.get_by_id(db, input_id)
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
        db_record = InputRecordCRUD.get_by_id(db, input_id)
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
        db_record = InputRecordCRUD.get_by_id(db, input_id)
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
        db_record = InputRecordCRUD.get_by_id(db, input_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: InputRecord) -> InputRecordSchema:
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
