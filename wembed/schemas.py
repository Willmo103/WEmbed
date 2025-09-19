from datetime import datetime

import llm
from docling_core.transforms.chunker.base import BaseChunk
from pydantic import BaseModel, Field, Json, computed_field
from sqlite_utils import Database

from wembed.file_scanner import ListFileOpts


class _BaseModel(BaseModel):
    class Config:
        from_attributes: bool = True

        arbitrary_types_allowed: bool = True



class ChunkModel(_BaseModel):
    index: int
    chunk: Json[BaseChunk]
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
    model: llm.models.EmbeddingModel | None = Field(
        None,
    )
    model_id: str | None = None
    create: bool = True


class ScanResult(_BaseModel):
    id: str
    root_path: str
    name: str
    scan_type: str
    files: list[str] | None
    scan_start: datetime
    scan_end: datetime
    duration: float
    options: Json[ListFileOpts]
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
