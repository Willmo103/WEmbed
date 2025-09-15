from sqlalchemy import (
    BINARY,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import BYTEA
from ._base import Base
import schemas


class InputModel(Base):
    __tablename__ = "inputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    errors = Column(String, nullable=True)
    added_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    def to_schema(self) -> schemas.InputOut:
        return schemas.InputOut(
            id=self.id,
            source=self.source,
            source_type=self.source_type,
            status=self.status,
            errors=self.errors,
            added_at=self.added_at.isoformat() if self.added_at else None,
            processed_at=self.processed_at.isoformat() if self.processed_at else None,
        )


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(ForeignKey("documents.id"), nullable=False)
    idx = Column(Integer, nullable=False)
    chunk = Column(String, nullable=False)
    embedding = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


class FileRecord(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    user = Column(String, nullable=False)
    name = Column(String, nullable=False)
    stem = Column(String, nullable=False)
    path = Column(String, nullable=False)
    relative_path = Column(String, nullable=False)
    suffix = Column(String, nullable=False)
    sha256 = Column(String, nullable=False, unique=True)
    md5 = Column(String, nullable=False)
    mode = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    content = Column(BYTEA, nullable=True)
    content_text = Column(Text, nullable=False)
    markdown = Column(Text, nullable=True)
    ctime_iso = Column(DateTime, nullable=False)
    mtime_iso = Column(DateTime, nullable=False)
    line_count = Column(Integer, nullable=False)
    uri = Column(String, nullable=False)
    mimetype = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default="now()")


class DocumentRecord(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_ref = Column(ForeignKey("inputs.id"), nullable=True)
    dl_doc = Column(String, nullable=True)
    markdown = Column(String, nullable=True)
    html = Column(String, nullable=True)
    text = Column(String, nullable=True)
    doctags = Column(String, nullable=True)
    chunks_json = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)


class FileLine(Base):
    __tablename__ = "file_lines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(ForeignKey("files.id"), nullable=False)
    file_repo_name = Column(String, nullable=False)
    file_repo_type = Column(String, nullable=False)
    line_number = Column(Integer, nullable=False)
    line_text = Column(Text, nullable=False)
    embedding = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


class MarkdownFpXref(Base):
    __tablename__ = "md_fp_xref"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_sha256 = Column(ForeignKey("files.sha256"), nullable=False, unique=True)
    file_uri = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    source_root = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    vault_path = Column(String, nullable=False)
    last_rendered = Column(DateTime, nullable=False)
