# file_record.py

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, computed_field
from sqlalchemy import DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from ._base import Base


class FileRecord(Base):
    __tablename__ = "dl_files"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_root: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    stem: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    relative_path: Mapped[str] = mapped_column(String, nullable=False)
    suffix: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    md5: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ctime_iso: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    mtime_iso: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    uri: Mapped[str] = mapped_column(String, nullable=False)
    mimetype: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default="now()"
    )


class FileRecordSchema(BaseModel):
    id: str
    version: int = 1
    source_type: str
    source_root: str
    source_name: str
    host: Optional[str] = None
    user: Optional[str] = None
    name: Optional[str] = None
    stem: Optional[str] = None
    path: Optional[str] = None
    relative_path: Optional[str] = None
    suffix: Optional[str] = None
    sha256: Optional[str] = None
    md5: Optional[str] = None
    mode: Optional[int] = None
    size: Optional[int] = None
    content: Optional[bytes] = None
    content_text: Optional[str] = None
    ctime_iso: Optional[datetime] = None
    mtime_iso: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    line_count: Optional[int] = None
    uri: Optional[str] = None
    mimetype: Optional[str] = None
    markdown: Optional[str] = None

    def bump_version(self):
        self.version += 1

    class Config:
        from_attributes = True


class FileLineSchema(BaseModel):
    file_id: str
    file_repo_name: str
    file_repo_type: str
    file_version: str
    line_number: int
    line_text: str
    embedding: Optional[list[float]] = None

    @computed_field
    @property
    def id(self) -> str:
        return f"{self.file_id}:{self.line_number}"

    class Config:
        from_attributes = True


class FileRecordCRUD:
    @staticmethod
    def create(db: Session, file_record: FileRecordSchema) -> FileRecord:
        db_record = FileRecord(
            id=file_record.id,
            version=file_record.version,
            source_type=file_record.source_type,
            source_root=file_record.source_root,
            source_name=file_record.source_name,
            host=file_record.host or "",
            user=file_record.user or "",
            name=file_record.name or "",
            stem=file_record.stem or "",
            path=file_record.path or "",
            relative_path=file_record.relative_path or "",
            suffix=file_record.suffix or "",
            sha256=file_record.sha256 or "",
            md5=file_record.md5 or "",
            mode=file_record.mode or 0,
            size=file_record.size or 0,
            content=file_record.content,
            content_text=file_record.content_text or "",
            markdown=file_record.markdown,
            ctime_iso=file_record.ctime_iso or file_record.created_at,
            mtime_iso=file_record.mtime_iso or file_record.created_at,
            line_count=file_record.line_count or 0,
            uri=file_record.uri or "",
            mimetype=file_record.mimetype or "",
            created_at=file_record.created_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, file_id: str) -> Optional[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.id == file_id).first()

    @staticmethod
    def get_by_sha256(db: Session, sha256: str) -> Optional[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.sha256 == sha256).first()

    @staticmethod
    def get_by_source_type(db: Session, source_type: str) -> list[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.source_type == source_type).all()

    @staticmethod
    def get_by_source_name(db: Session, source_name: str) -> list[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.source_name == source_name).all()

    @staticmethod
    def get_by_host(db: Session, host: str) -> list[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.host == host).all()

    @staticmethod
    def get_by_suffix(db: Session, suffix: str) -> list[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.suffix == suffix).all()

    @staticmethod
    def get_by_mimetype(db: Session, mimetype: str) -> list[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.mimetype == mimetype).all()

    @staticmethod
    def search_by_name(db: Session, name_pattern: str) -> list[FileRecord]:
        return db.query(FileRecord).filter(FileRecord.name.contains(name_pattern)).all()

    @staticmethod
    def search_by_content(db: Session, search_text: str) -> list[FileRecord]:
        return (
            db.query(FileRecord)
            .filter(FileRecord.content_text.contains(search_text))
            .all()
        )

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[FileRecord]:
        return db.query(FileRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, file_id: str, file_record: FileRecordSchema
    ) -> Optional[FileRecord]:
        db_record = FileRecordCRUD.get_by_id(db, file_id)
        if db_record:
            for key, value in file_record.model_dump(
                exclude_unset=True, exclude={"id"}
            ).items():
                if value is not None:
                    setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_version(db: Session, file_id: str) -> Optional[FileRecord]:
        db_record = FileRecordCRUD.get_by_id(db, file_id)
        if db_record:
            db_record.version += 1
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_markdown(
        db: Session, file_id: str, markdown: str
    ) -> Optional[FileRecord]:
        db_record = FileRecordCRUD.get_by_id(db, file_id)
        if db_record:
            db_record.markdown = markdown
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, file_id: str) -> bool:
        db_record = FileRecordCRUD.get_by_id(db, file_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: FileRecord) -> FileRecordSchema:
        return FileRecordSchema(
            id=record.id,
            version=record.version,
            source_type=record.source_type,
            source_root=record.source_root,
            source_name=record.source_name,
            host=record.host,
            user=record.user,
            name=record.name,
            stem=record.stem,
            path=record.path,
            relative_path=record.relative_path,
            suffix=record.suffix,
            sha256=record.sha256,
            md5=record.md5,
            mode=record.mode,
            size=record.size,
            content=record.content,
            content_text=record.content_text,
            ctime_iso=record.ctime_iso,
            mtime_iso=record.mtime_iso,
            created_at=record.created_at,
            line_count=record.line_count,
            uri=record.uri,
            mimetype=record.mimetype,
            markdown=record.markdown,
        )
