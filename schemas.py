from datetime import datetime, timezone
from typing import List, Optional, Set

import llm
from pydantic import BaseModel, Field, computed_field
from sqlalchemy import Table
from sqlite_utils import Database
from docling_core.types.doc.document import DoclingDocument
from docling_core.transforms.chunker.base import BaseChunk


class _BaseModel(BaseModel):
    class Config:
        from_attributes: bool = True


class FileLineSchema(_BaseModel):
    file_id: str
    file_repo_name: str
    file_repo_type: str
    file_version: str
    line_number: int
    line_text: str
    embedding: Optional[List[float]] = None

    @computed_field
    @property
    def id(self) -> str:
        return f"{self.file_id}:{self.line_number}"


class FileRecordSchema(_BaseModel):
    id: str
    version: int
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
    mode: Optional[str] = None
    size: Optional[int] = None
    content: Optional[bytes] = None
    content_text: Optional[str] = None
    ctime_iso: Optional[str] = None
    mtime_iso: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.timezone.utc)
    )
    line_count: Optional[int] = None
    uri: Optional[str] = None
    mimetype: Optional[str] = None
    markdown: Optional[str] = None
    version: Optional[int] = None

    def bump_version(self):
        if self.version is not None:
            self.version += 1


class ChunkRecordModel(_BaseModel):
    id: int
    document_id: int
    text_chunk: str  # Renamed from 'chunk' to avoid ambiguity
    idx: int
    embedding: List[float]
    created_at: datetime


class DocumentRecordModel(_BaseModel):
    id: int
    source: str
    source_type: str
    source_ref: Optional[int] = None
    dl_doc: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    doctags: Optional[str] = None
    chunks_json: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


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


class ScanResultList(_BaseModel):
    results: list[ScanResult]

    def add_result(self, result: ScanResult):
        self.results.append(result)

    def iter_results(self):
        for result in self.results:
            yield result


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
