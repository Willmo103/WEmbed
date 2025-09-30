"""
(File: src/wembed/db/file_record.py)
SQLAlchemy models and Pydantic schemas for file records and file lines,
along with Repository classes for CRUD operations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .file_line import FileLineRecord, FileLineSchema
from .tables.tagged_items_table import TaggedItemSchema, TaggedItemsTable
from .tag_record import TagRecord


class FileRecord(Base):
    """
    SQLAlchemy model for the 'dl_files' table, representing file records.

    Attributes:
        id (str): Unique identifier for the file (primary key).
        version (int): Version number of the file record.
        source_type (str): Type of the source (e.g., 'git', 'local').
        source_root (str): Root path of the source.
        source_name (str): Name of the source (e.g., repository name).
        host (str): Hostname where the file is located.
        user (str): User associated with the file.
        name (str): Name of the file.
        stem (str): Stem of the file name (name without suffix).
        path (str): Full path to the file.
        relative_path (str): Path relative to the source root.
        suffix (str): File extension/suffix.
        sha256 (str): SHA-256 hash of the file content (unique).
        md5 (str): MD5 hash of the file content.
        mode (int): File mode/permissions.
        size (int): Size of the file in bytes.
        content (bytes, optional): Binary content of the file.
        content_text (str): Text content of the file.
        markdown (str, optional): Markdown representation of the file content.
        ctime_iso (datetime): Creation time of the file in ISO format.
        mtime_iso (datetime): Last modification time of the file in ISO format.
        line_count (int): Number of lines in the file.
        uri (str): URI of the file.
        mimetype (str): MIME type of the file.
        created_at (datetime): Timestamp when the record was created.

        relationships:
        - tags: Relationship to TaggedItemsTable for associated tags.
    """

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
    tags: Mapped[List["TagRecord"]] = relationship(
        secondary=TaggedItemsTable.__table__,
        primaryjoin=id == TaggedItemsTable.tagged_item_id,
        secondaryjoin=TagRecord.id == TaggedItemsTable.tag_id,
        back_populates="files",
    )


class FileRecordSchema(BaseModel):
    id: str = Field(..., description="Unique identifier for the file")
    version: int = Field(1, description="Version number of the file record")
    source_type: str = Field(
        ...,
        max_length=50,
        description="Type of the source (e.g., 'repo', 'vault', 'documentation')",
    )
    source_root: str = Field(..., description="Root path of the source")
    source_name: str = Field(
        ..., description="Name of the source (e.g., repository name)"
    )
    host: Optional[str] = Field(None, description="Hostname where the file is located")
    user: Optional[str] = Field(None, description="User associated with the file")
    name: Optional[str] = Field(None, description="Name of the file")
    stem: Optional[str] = Field(
        None, description="Stem of the file name (name without suffix)"
    )
    path: Optional[str] = Field(None, description="Full path to the file")
    relative_path: Optional[str] = Field(
        None, description="Path relative to the source root"
    )
    suffix: Optional[str] = Field(None, description="File extension/suffix")
    sha256: Optional[str] = Field(
        None, description="SHA-256 hash of the file content (unique)"
    )
    md5: Optional[str] = Field(None, description="MD5 hash of the file content")
    mode: Optional[int] = Field(None, description="File mode/permissions")
    size: Optional[int] = Field(None, description="Size of the file in bytes")
    content: Optional[bytes] = Field(None, description="Binary content of the file")
    content_text: Optional[str] = Field(None, description="Text content of the file")
    ctime_iso: Optional[datetime] = Field(
        None, description="Creation time of the file (ISO format)"
    )
    mtime_iso: Optional[datetime] = Field(
        None, description="Last modified time of the file (ISO format)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of when the record was created",
    )
    line_count: Optional[int] = Field(None, description="Number of lines in the file")
    uri: Optional[str] = Field(None, description="URI of the file on the host system")
    mimetype: Optional[str] = Field(None, description="MIME type of the file")
    markdown: Optional[str] = Field(None, description="Markdown content of the file")
    tags: Optional[List[TaggedItemSchema]] = Field(
        [], description="List of associated tags"
    )

    def bump_version(self) -> None:
        self.version += 1

    class Config:
        """Pydantic configuration to allow ORM mode."""

        from_attributes = True


class FileRecordRepo:
    """
    Repository class for performing CRUD operations on FileRecord.

    Methods:
    - create: Create a new file record.
    - get_by_id: Retrieve a file record by its ID.
    - get_by_sha256: Retrieve a file record by its SHA-256 hash.
    - get_by_source_type: Retrieve file records by source type.
    - get_by_source_name: Retrieve file records by source name.
    - get_by_host: Retrieve file records by host.
    - get_by_suffix: Retrieve file records by file suffix.
    - get_by_mimetype: Retrieve file records by MIME type.
    - search_by_name: Search file records by name pattern.
    - search_by_content: Search file records by content text.
    - get_all: Retrieve all file records with pagination.
    - update: Update an existing file record.
    - update_version: Increment the version of a file record.
    - update_markdown: Update the markdown content of a file record.
    - delete: Delete a file record by its ID.
    - to_schema: Convert a FileRecord to its corresponding FileRecordSchema.
    """

    _db_srvc: "DbService"

    def __init__(self, db_svc: "DbService"):
        self._db_srvc = db_svc

    def create(self, file_record: FileRecordSchema) -> FileRecord:
        """
        Create a new file record in the database.

        Args:
            file_record (FileRecordSchema): Pydantic schema representing the file record to create.

        Returns:
            FileRecord: The created FileRecord SQLAlchemy model instance.
        """
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
        with self._db_srvc.get_session()() as db:
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            return db_record

    def get_by_id(self, file_id: str) -> Optional[FileRecord]:
        """
        Retrieve a file record by its ID.

        Args:
            file_id (str): The ID of the file record to retrieve.

        Returns:
            Optional[FileRecord]: The FileRecord instance if found, else None.
        """
        with self._db_srvc.get_session()() as db:
            return db.query(FileRecord).filter(FileRecord.id == file_id).first()

    def get_by_sha256(self, sha256: str) -> Optional[FileRecord]:
        """
        Retrieve a file record by its SHA-256 hash.

        Args:
            sha256 (str): The SHA-256 hash of the file record to retrieve.

        Returns:
            Optional[FileRecord]: The FileRecord instance if found, else None.
        """
        with self._db_srvc.get_session()() as db:
            return db.query(FileRecord).filter(FileRecord.sha256 == sha256).first()

    def get_by_source_type(self, source_type: str) -> List[FileRecordSchema]:
        """
        Retrieve file records by their source type.

        Args:
            source_type (str): The source type to filter file records.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the source type.
        """
        with self._db_srvc.get_session()() as db:
            results = (
                db.query(FileRecord).filter(FileRecord.source_type == source_type).all()
            )
            try:
                return [FileRecordSchema(**r.__dict__) for r in results]
            except Exception:
                db.rollback()
            return []

    def get_by_source_name(self, source_name: str) -> List[FileRecordSchema]:
        """
        Retrieve file records by their source name.

        Args:
            source_name (str): The source name to filter file records.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the source name.
        """
        with self._db_srvc.get_session()() as db:
            results = (
                db.query(FileRecord).filter(FileRecord.source_name == source_name).all()
            )
            try:
                records = [FileRecord(**r.__dict__) for r in results]
                return [FileRecordRepo.to_schema(r) for r in records]
            except Exception:
                db.rollback()
                return []

    def get_by_host(self, host: str) -> List[FileRecordSchema]:
        """
        Retrieve file records by their host.

        Args:
            host (str): The host to filter file records.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the host.
        """
        with self._db_srvc.get_session()() as db:
            records = db.query(FileRecord).filter(FileRecord.host == host).all()
            try:
                return [FileRecordSchema(**r.__dict__) for r in records]
            except Exception:
                db.rollback()
                return []

    def get_by_suffix(self, suffix: str) -> List[FileRecordSchema]:
        """
        Retrieve file records by their file suffix.

        Args:
            suffix (str): The file suffix to filter file records.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the suffix.
        """
        with self._db_srvc.get_session()() as db:
            results = db.query(FileRecord).filter(FileRecord.suffix == suffix).all()
            try:
                records = [FileRecord(**r.__dict__) for r in results]
                return [FileRecordRepo.to_schema(r) for r in records]
            except Exception:
                db.rollback()
                return []

    def get_by_mimetype(self, mimetype: str) -> List[FileRecordSchema]:
        """
        Retrieve file records by their MIME type.

        Args:
            mimetype (str): The MIME type to filter file records.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the MIME type.
        """
        with self._db_srvc.get_session()() as db:
            results = db.query(FileRecord).filter(FileRecord.mimetype == mimetype).all()
            try:
                records = [FileRecord(**r.__dict__) for r in results]
                return [FileRecordRepo.to_schema(r) for r in records]
            except Exception:
                db.rollback()
                return []

    def search_by_name(self, name_pattern: str) -> List[FileRecordSchema]:
        """
        Search for file records by their name.

        Args:
            name_pattern (str): The name pattern to search for.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the name pattern.
        """
        with self._db_srvc.get_session()() as db:
            results = (
                db.query(FileRecord)
                .filter(FileRecord.name.contains(name_pattern))
                .all()
            )
            try:
                records = [FileRecord(**r.__dict__) for r in results]
                return [FileRecordRepo.to_schema(r) for r in records]
            except Exception:
                db.rollback()
                return []

    def search_by_content(self, search_text: str) -> List[FileRecordSchema]:
        """
        Search for file records by their content.

        Args:
            search_text (str): The content text to search for.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects matching the content text.
        """
        with self._db_srvc.get_session()() as db:
            results = (
                db.query(FileRecord)
                .filter(FileRecord.content_text.contains(search_text))
                .all()
            )
            try:
                records = [FileRecord(**r.__dict__) for r in results]
                return [FileRecordRepo.to_schema(r) for r in records]
            except Exception:
                db.rollback()
                return []

    def get_all(self, skip: int = 0, limit: int = 100) -> List[FileRecordSchema]:
        """
        Retrieve all file records with pagination.

        Args:
            skip (int): Number of records to skip (for pagination).
            limit (int): Maximum number of records to return.

        Returns:
            List[FileRecordSchema]: List of FileRecordSchema objects.
        """
        with self._db_srvc.get_session()() as db:
            results = db.query(FileRecord).offset(skip).limit(limit).all()
            try:
                records = [FileRecord(**r.__dict__) for r in results]
                return [FileRecordRepo.to_schema(r) for r in records]
            except Exception:
                db.rollback()
                return []

    def update(
        self, file_id: str, file_record: FileRecordSchema
    ) -> Optional[FileRecord]:
        """
        Update an existing file record in the database.

        Args:
            file_id (str): The ID of the file record to update.
            file_record (FileRecordSchema): Pydantic schema with updated fields.

        Returns:
            Optional[FileRecord]: The updated file record or None if not found.
        """
        with self._db_srvc.get_session()() as db:
            db_record = FileRecordRepo.get_by_id(db, file_id)
            if db_record:
                for key, value in file_record.model_dump(
                    exclude_unset=True, exclude={"id"}
                ).items():
                    if value is not None:
                        setattr(db_record, key, value)
                db.commit()
                db.refresh(db_record)
            return db_record

    def update_version(self, file_id: str) -> Optional[FileRecord]:
        """
        Increment the version of a file record.

        Args:
            file_id (str): The ID of the file record to update.

        Returns:
            Optional[FileRecord]: The updated file record or None if not found.
        """
        with self._db_srvc.get_session()() as db:
            db_record = FileRecordRepo.get_by_id(db, file_id)
            if db_record:
                db_record.version += 1
                db.commit()
                db.refresh(db_record)
            return db_record

    def update_markdown(self, file_id: str, markdown: str) -> Optional[FileRecord]:
        """
        Update the markdown content of a file record.

        Args:
            file_id (str): The ID of the file record to update.
            markdown (str): The new markdown content.

        Returns:
            Optional[FileRecord]: The updated file record or None if not found.
        """
        with self._db_srvc.get_session()() as db:
            db_record = FileRecordRepo.get_by_id(db, file_id)
            if db_record:
                db_record.markdown = markdown
                db.commit()
                db.refresh(db_record)
            return db_record

    def delete(self, file_id: str) -> bool:
        """
        Delete a file record by its ID.
        Args:
            file_id (str): The ID of the file record to delete.
        Returns:
            bool: True if the record was deleted, False if not found.
        """
        with self._db_srvc.get_session()() as db:
            db_record = FileRecordRepo.get_by_id(db, file_id)
            if db_record:
                db.delete(db_record)
                db.commit()
                return True
            return False

    def to_schema(record: FileRecord) -> FileRecordSchema:
        """
        Convert a FileRecord SQLAlchemy model instance to a FileRecordSchema Pydantic model.

        Args:
            record (FileRecord): The FileRecord instance to convert.

        Returns:
            FileRecordSchema: The corresponding FileRecordSchema instance.

        """
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
            tags=(
                [TaggedItemSchema(**t.__dict__) for t in record.tags]
                if record.tags
                else []
            ),
        )
