from datetime import datetime
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from ._base import Base

# class FileSources(Base):
#     __tablename__ = "dl_file_sources"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     file_id = Column(ForeignKey("dl_files.id"), nullable=False)
#     name = Column(String, nullable=False)
#     type = Column(String, nullable=False)
#     root = Column(String, nullable=False)
#     user = Column(String, nullable=False)
#     host = Column(String, nullable=False)


class ScanResultRecord(Base):
    __tablename__ = "dl_scan_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    root_path = Column(String, nullable=False)
    scan_type = Column(String, nullable=False)
    scan_name = Column(String, nullable=True)
    files = Column(JSON, nullable=True)
    scan_start = Column(DateTime(timezone=True), nullable=False)
    scan_end = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)
    options = Column(JSON, nullable=True)
    user = Column(String, nullable=False)
    host = Column(String, nullable=False)


class VaultRecord(Base):
    __tablename__ = "dl_vault"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    root_path = Column(String, nullable=False)
    files = Column(JSON, nullable=True)
    file_count = Column(Integer, nullable=False, default=0)
    indexed_at = Column(DateTime(timezone=True), nullable=True)


class RepoRecord(Base):
    __tablename__ = "dl_repo"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    root_path = Column(String, nullable=False)
    files = Column(JSON, nullable=True)
    file_count = Column(Integer, nullable=False, default=0)
    indexed_at = Column(DateTime(timezone=True), nullable=True)


class DocumentIndexRecord(Base):
    __tablename__ = "dl_document_index"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(ForeignKey("dl_files.id"), nullable=False)
    last_rendered = Column(DateTime(timezone=True), nullable=True)


class InputRecord(Base):
    """
    This Class represents the records that need to be processed from Markdown, via the FileRecord.markdown Content
    into a DocumentRecord for that File

    Attributes:
    id: int:: The unique identifier for the input record
    source_type: str:: The SourceType enum value representing the origin of the input ["Vault", "Repo", "Documentation", etc. ]
    `see: ingestor-core/enums.SourceTypes`
    """

    __tablename__ = "dl_inputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    errors = Column(Text, nullable=True)
    added_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )
    processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    output_doc_id = Column(ForeignKey("dl_documents.id"), nullable=True)
    input_file_id = Column(ForeignKey("dl_files.id"), nullable=True)


class ChunkRecord(Base):
    __tablename__ = "dl_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(ForeignKey("dl_documents.id"), nullable=False, index=True)
    idx = Column(Integer, nullable=False)
    text_chunk = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )


class FileRecord(Base):
    __tablename__ = "dl_files"
    id = Column(String, primary_key=True)
    version = Column(Integer, nullable=False, default=1)
    source_type = Column(String, nullable=False)
    source_root = Column(String, nullable=False)
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
    content = Column(LargeBinary, nullable=True)
    content_text = Column(Text, nullable=False)
    markdown = Column(Text, nullable=True)
    ctime_iso = Column(DateTime, nullable=False)
    mtime_iso = Column(DateTime, nullable=False)
    line_count = Column(Integer, nullable=False)
    uri = Column(String, nullable=False)
    mimetype = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default="now()")


class DocumentRecord(Base):
    __tablename__ = "dl_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_ref = Column(ForeignKey("dl_inputs.id"), nullable=True)
    dl_doc = Column(Text, nullable=True)
    markdown = Column(Text, nullable=True)
    html = Column(Text, nullable=True)
    text = Column(Text, nullable=True)
    doctags = Column(Text, nullable=True)
    chunks_json = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(datetime.timezone.utc),
    )


class FileLineRecord(Base):
    __tablename__ = "dl_filelines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(ForeignKey("dl_files.id"), nullable=False, index=True)
    file_repo_name = Column(String, nullable=False)
    file_repo_type = Column(String, nullable=False)
    line_number = Column(Integer, nullable=False)
    line_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )
