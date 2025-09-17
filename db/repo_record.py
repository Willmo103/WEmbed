# repo_record.py

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, Session
from pydantic import BaseModel
from ._base import Base


class RepoRecord(Base):
    __tablename__ = "dl_repo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    root_path: Mapped[str] = mapped_column(String, nullable=False)
    files: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RepoRecordSchema(BaseModel):
    id: Optional[int] = None
    name: str
    host: str
    root_path: str
    files: Optional[List[str]] = None
    file_count: int = 0
    indexed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RepoRecordCRUD:
    @staticmethod
    def create(db: Session, repo: RepoRecordSchema) -> RepoRecord:
        db_record = RepoRecord(
            name=repo.name,
            host=repo.host,
            root_path=repo.root_path,
            files=repo.files,
            file_count=repo.file_count,
            indexed_at=repo.indexed_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, repo_id: int) -> Optional[RepoRecord]:
        return db.query(RepoRecord).filter(RepoRecord.id == repo_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[RepoRecord]:
        return db.query(RepoRecord).filter(RepoRecord.name == name).first()

    @staticmethod
    def get_by_host(db: Session, host: str) -> List[RepoRecord]:
        return db.query(RepoRecord).filter(RepoRecord.host == host).all()

    @staticmethod
    def get_by_root_path(db: Session, root_path: str) -> Optional[RepoRecord]:
        return db.query(RepoRecord).filter(RepoRecord.root_path == root_path).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[RepoRecord]:
        return db.query(RepoRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, repo_id: int, repo: RepoRecordSchema
    ) -> Optional[RepoRecord]:
        db_record = RepoRecordCRUD.get_by_id(db, repo_id)
        if db_record:
            for key, value in repo.model_dump(
                exclude_unset=True, exclude={"id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, repo_id: int) -> bool:
        db_record = RepoRecordCRUD.get_by_id(db, repo_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def update_file_count(
        db: Session, repo_id: int, file_count: int
    ) -> Optional[RepoRecord]:
        db_record = RepoRecordCRUD.get_by_id(db, repo_id)
        if db_record:
            db_record.file_count = file_count
            db_record.indexed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def to_schema(record: RepoRecord) -> RepoRecordSchema:
        return RepoRecordSchema(
            id=record.id,
            name=record.name,
            host=record.host,
            root_path=record.root_path,
            files=record.files,
            file_count=record.file_count,
            indexed_at=record.indexed_at,
        )
