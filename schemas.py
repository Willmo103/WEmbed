from datetime import datetime, timezone
from typing import Optional, Set

import llm
from pydantic import BaseModel, computed_field
from sqlalchemy import Table
from sqlite_utils import Database
from docling_core.types.doc.document import DoclingDocument
from docling_core.transforms.chunker.base import BaseChunk


class _BaseModel(BaseModel):
    class Config:
        from_attributes: bool = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            set: lambda v: "[" + ", ".join(v) + "]" if v else "[]",
            list: lambda v: "[" + ", ".join(v) + "]" if v else "[]",
            Exception: lambda v: str(v) if v else None,
        }


class FileLine(_BaseModel):
    file_id: str
    file_repo_name: str
    file_repo_type: str
    file_version: str
    line_number: int
    line_text: str
    embedding: Optional[list[float]] = None

    @computed_field
    def id(self) -> str:
        return f"{self.file_id}:{self.line_number}"


class FileRecord(_BaseModel):
    id: str
    version: int
    source: str
    source_root: str
    source_name: str
    host: str | None
    user: str | None
    name: str | None
    stem: str | None
    path: str | None
    relative_path: str | None
    suffix: str | None
    sha256: str | None
    md5: str | None
    mode: str | None
    size: int | None
    content: bytes | None
    content_text: str | None
    ctime_iso: str | None
    mtime_iso: str | None
    created_at: datetime = datetime.now(tz=timezone.utc)
    line_count: int | None
    uri: Optional[str] | None
    mimetype: str | None
    markdown: str | None

    def bump_version(self):
        self.version += 1


class DocumentRecordModel(_BaseModel):
    id: int
    source: str
    source_type: str
    source_ref: int | None
    dl_doc: str | None
    markdown: str | None
    html: str | None
    text: str | None
    doctags: str | None
    chunks_json: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
        },
    }


class ChunkRecordModel(_BaseModel):
    id: int
    document_id: int
    chunk: str
    embedding: list[float]
    created_at: str


class ChunkModel(_BaseModel):
    index: int
    chunk: BaseChunk
    embedding: list[float]


class ChunkList(_BaseModel):
    chunks: list[ChunkModel]


class DocumentOut(_BaseModel):
    id: int
    source: str
    source_type: str
    source_ref: str | None
    dl_doc: str | None
    markdown: str | None
    html: str | None
    text: str | None
    doctags: str | None
    chunks: ChunkList | None
    created_at: str
    updated_at: str | None


class StringContentOut(_BaseModel):
    source: str
    source_type: str
    source_ref: str | None
    created_at: str
    content: str | None


class LlmCollectionParams(_BaseModel):
    name: str
    db: Database | None = None
    model: llm.models.EmbeddingModel | None = None
    model_id: str | None = None
    create: bool = True

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {},
    }


class ScanResult(_BaseModel):
    id: str
    root: str
    name: str
    scan_type: str
    files: list[str] | None
    scan_start: datetime
    scan_end: datetime
    duration: float
    options: dict
    user: str
    host: str

    @computed_field
    def total_files(self) -> int:
        return len(self.files)


class InputOut(_BaseModel):
    id: int
    source: str
    source_type: str
    status: str
    errors: list[str] | None = None
    files: list[str] | None = None
    added_at: datetime
    processed_at: datetime
    total_files: int
