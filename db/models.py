from datetime import datetime
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from ._base import Base
import schemas


class InputModel(Base):
    __tablename__ = "inputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    errors = Column(
        Text, nullable=True
    )
    added_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    output_doc_id = Column(ForeignKey("documents.id"), nullable=True)
    input_file_id = Column(ForeignKey("files.id"), nullable=True)


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        ForeignKey("documents.id"), nullable=False, index=True
    )
    idx = Column(Integer, nullable=False)
    text_chunk = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )

    def to_schema(self) -> schemas.ChunkRecordModel:
        return schemas.ChunkRecordModel(
            id=self.id,
            document_id=self.document_id,
            idx=self.idx,
            text_chunk=self.text_chunk,
            embedding=self.embedding,  # This will be a Python list automatically
            created_at=self.created_at,
        )


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
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_ref = Column(ForeignKey("inputs.id"), nullable=True)
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


class FileLine(Base):
    __tablename__ = "file_lines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(ForeignKey("files.id"), nullable=False, index=True)
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
