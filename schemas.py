from datetime import datetime, timezone
from typing import Optional, Set

import llm
from pydantic import BaseModel, computed_field
from sqlalchemy import Table
from sqlite_utils import Database
from docling_core.types.doc.document import DoclingDocument
from docling_core.transforms.chunker.base import BaseChunk


class FileLine(BaseModel):
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


class FileRecord(BaseModel):
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

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
        },
    }

    def bump_version(self):
        self.version += 1


class DocumentRecordModel(BaseModel):
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

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            "ChunkRecordModel": lambda v: (v.model_dump_json(indent=2) if v else None),
        }


class ChunkRecordModel(BaseModel):
    id: int
    document_id: int
    chunk: str
    embedding: list[float]
    created_at: str

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class ChunkModel(BaseModel):
    index: int
    chunk: BaseChunk
    embedding: list[float]


class ChunkList(BaseModel):
    chunks: list[ChunkModel]


class DocumentOut(BaseModel):
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


class StringContentOut(BaseModel):
    source: str
    source_type: str
    source_ref: str | None
    created_at: str
    content: str | None


class LlmCollectionParams(BaseModel):
    name: str
    db: Database | None = None
    model: llm.models.EmbeddingModel | None = None
    model_id: str | None = None
    create: bool = True

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            llm.models.EmbeddingModel: lambda v: v.model_id if v else str(v),
        },
    }


class ScanResult(BaseModel):
    root: str
    name: str
    files: Set[str]
    scan_start: datetime
    scan_end: datetime
    duration: float
    options: dict
    error: str | None

    @computed_field
    def total_files(self) -> int:
        return len(self.files)

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class InputOut(BaseModel):
    id: int
    source: str
    source_type: str
    status: str
    errors: str | None
    added_at: datetime
    processed_at: datetime
