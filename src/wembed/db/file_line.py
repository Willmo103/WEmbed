from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class FileLineRecord(Base):
    __tablename__ = "dl_filelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(
        ForeignKey("dl_files.id"), nullable=False, index=True
    )
    file_repo_name: Mapped[str] = mapped_column(String, nullable=False)
    file_repo_type: Mapped[str] = mapped_column(String, nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    line_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class FileLineSchema(BaseModel):
    id: Optional[int] = None
    file_id: str
    file_repo_name: str
    file_repo_type: str
    file_version: str
    line_number: int
    line_text: str
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @computed_field
    @property
    def composite_id(self) -> str:
        return f"{self.file_id}:{self.line_number}"

    class Config:
        from_attributes = True


class FileLineCRUD:
    @staticmethod
    def create(db: Session, file_line: FileLineSchema) -> FileLineRecord:
        db_record = FileLineRecord(
            file_id=file_line.file_id,
            file_repo_name=file_line.file_repo_name,
            file_repo_type=file_line.file_repo_type,
            line_number=file_line.line_number,
            line_text=file_line.line_text,
            embedding=file_line.embedding,
            created_at=file_line.created_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def create_batch(
        db: Session, file_lines: List[FileLineSchema]
    ) -> List[FileLineRecord]:
        db_records = []
        for file_line in file_lines:
            db_record = FileLineRecord(
                file_id=file_line.file_id,
                file_repo_name=file_line.file_repo_name,
                file_repo_type=file_line.file_repo_type,
                line_number=file_line.line_number,
                line_text=file_line.line_text,
                embedding=file_line.embedding,
                created_at=file_line.created_at,
            )
            db_records.append(db_record)

        db.add_all(db_records)
        db.commit()
        for record in db_records:
            db.refresh(record)
        return db_records

    @staticmethod
    def get_by_id(db: Session, line_id: int) -> Optional[FileLineRecord]:
        return db.query(FileLineRecord).filter(FileLineRecord.id == line_id).first()

    @staticmethod
    def get_by_file_id(db: Session, file_id: str) -> List[FileLineRecord]:
        return (
            db.query(FileLineRecord)
            .filter(FileLineRecord.file_id == file_id)
            .order_by(FileLineRecord.line_number)
            .all()
        )

    @staticmethod
    def get_by_file_and_line(
        db: Session, file_id: str, line_number: int
    ) -> Optional[FileLineRecord]:
        return (
            db.query(FileLineRecord)
            .filter(
                FileLineRecord.file_id == file_id,
                FileLineRecord.line_number == line_number,
            )
            .first()
        )

    @staticmethod
    def get_by_repo_name(db: Session, repo_name: str) -> List[FileLineRecord]:
        return (
            db.query(FileLineRecord)
            .filter(FileLineRecord.file_repo_name == repo_name)
            .all()
        )

    @staticmethod
    def get_by_repo_type(db: Session, repo_type: str) -> List[FileLineRecord]:
        return (
            db.query(FileLineRecord)
            .filter(FileLineRecord.file_repo_type == repo_type)
            .all()
        )

    @staticmethod
    def search_by_text(db: Session, search_text: str) -> List[FileLineRecord]:
        return (
            db.query(FileLineRecord)
            .filter(FileLineRecord.line_text.contains(search_text))
            .all()
        )

    @staticmethod
    def get_lines_with_embeddings(db: Session) -> List[FileLineRecord]:
        return (
            db.query(FileLineRecord).filter(FileLineRecord.embedding.is_not(None)).all()
        )

    @staticmethod
    def get_lines_without_embeddings(db: Session) -> List[FileLineRecord]:
        return db.query(FileLineRecord).filter(FileLineRecord.embedding.is_(None)).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[FileLineRecord]:
        return db.query(FileLineRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, line_id: int, file_line: FileLineSchema
    ) -> Optional[FileLineRecord]:
        db_record = FileLineCRUD.get_by_id(db, line_id)
        if db_record:
            for key, value in file_line.model_dump(
                exclude_unset=True, exclude={"id", "composite_id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_embedding(
        db: Session, file_id: str, line_number: int, embedding: List[float]
    ) -> Optional[FileLineRecord]:
        db_record = FileLineCRUD.get_by_file_and_line(db, file_id, line_number)
        if db_record:
            db_record.embedding = embedding
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, line_id: int) -> bool:
        db_record = FileLineCRUD.get_by_id(db, line_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_by_file_id(db: Session, file_id: str) -> int:
        deleted_count = (
            db.query(FileLineRecord).filter(FileLineRecord.file_id == file_id).delete()
        )
        db.commit()
        return deleted_count

    @staticmethod
    def delete_by_file_and_line(db: Session, file_id: str, line_number: int) -> bool:
        db_record = FileLineCRUD.get_by_file_and_line(db, file_id, line_number)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def get_line_count_by_file(db: Session, file_id: str) -> int:
        return (
            db.query(FileLineRecord).filter(FileLineRecord.file_id == file_id).count()
        )

    @staticmethod
    def to_schema(record: FileLineRecord) -> FileLineSchema:
        return FileLineSchema(
            id=record.id,
            file_id=record.file_id,
            file_repo_name=record.file_repo_name,
            file_repo_type=record.file_repo_type,
            file_version="1",  # Default version since it's not in the record
            line_number=record.line_number,
            line_text=record.line_text,
            embedding=record.embedding,
            created_at=record.created_at,
        )
