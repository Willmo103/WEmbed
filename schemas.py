from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, computed_field
from sqlite_utils import Database
from docling_core.types.doc.document import DoclingDocument
from docling_core.transforms.chunker.base import BaseChunk


class FileLine(BaseModel):
    file_id: str
    file_repo_name: str
    file_repo_type: str
    line_number: int
    line_text: str
    embedding: Optional[list[float]] = None

    @computed_field
    def id(self) -> str:
        return f"{self.file_id}:{self.line_number}"

    def save_to_sqlite(self, db: Database):
        db["file_lines"].insert(self.model_dump(), pk="id", replace=True, alter=True)


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
    created_at: str | None
    line_count: int | None
    uri: Optional[str] | None
    mimetype: str | None
    markdown: str | None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    def bump_version(self):
        self.version += 1

    def save_to_sqlite(self, db: Database):
        db["files"].insert(self.model_dump(), pk="id", replace=True, alter=True)
        self.save_lines_to_sqlite(db)

    def save_lines_to_sqlite(self, db: Database):
        lines = self.content_text.splitlines()
        for i, line in enumerate(lines):
            file_line = FileLine(
                file_id=self.id,
                file_repo_name=self.source_name,
                file_repo_type=self.source,
                line_number=i + 1,
                line_text=line,
            )
            file_line.save_to_sqlite(db)


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
    created_at: str

    class Config:
        from_attributes = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            "ChunkRecordModel": lambda v: (
                v.model_dump_json(indent=2) if v else None
            ),
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
    created_at: str = datetime.now(tz=timezone.utc).isoformat()


class StringContentOut(BaseModel):
    source: str
    source_type: str
    source_ref: str | None
    created_at: str


class MarkdownOut(StringContentOut):
    markdown: str


class HtmlOut(StringContentOut):
    html: str


class TextOut(StringContentOut):
    text: str


class DoclingDocOut(StringContentOut):
    dl_doc: str | None


class ChunksJsonOut(StringContentOut):
    chunks_json: str | None


class DoctagsOut(StringContentOut):
    doctags: str | None
