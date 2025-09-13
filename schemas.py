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

    def save_to_sqlite(self, db: Database, table_name: str = "file_lines"):
        db[table_name].insert(self.model_dump(), pk="id", replace=True, alter=True)

    def delete_from_sqlite(self, db: Database, table_name: str = "file_lines"):
        db[table_name].delete(where={"id": self.id})

    def update_in_sqlite(self, db: Database, table_name: str = "file_lines"):
        db[table_name].upsert(self.model_dump(), pk="id", alter=True)

    def update_embedding(self, db: Database, table_name: str = "file_lines"):
        db[table_name].update({"embedding": self.embedding}, where={"id": self.id})


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

    def save_to_sqlite(self, db: Database, table_name: str = "files"):
        db[table_name].insert(self.model_dump(), pk="id", replace=True, alter=True)
        self.save_lines_to_sqlite(db)

    def delete_from_sqlite(self, db: Database, table_name: str = "files"):
        db[table_name].delete({"id": self.id})

    def update_in_sqlite(self, db: Database, table_name: str = "files"):
        self.updated_at = datetime.now(tz=timezone.utc)
        db[table_name].upsert(self.model_dump(), pk="id", alter=True)

    def table(db: Database, table_name: str = "files") -> Table:
        return db[table_name]

    @classmethod
    def from_sqlite(
        cls, db: Database, file_id: str, table_name: str = "files"
    ) -> Optional["FileRecord"]:
        data = db[table_name].get(where={"id": file_id})
        if data:
            return cls(**data)
        return None


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

    def save_to_sqlite(self, db: Database, tablename: str = "documents"):
        db[tablename].insert(self.model_dump(), pk="id", replace=True, alter=True)

    def delete_from_sqlite(self, db: Database, tablename: str = "documents"):
        db[tablename].delete(where={"id": self.id})

    def update_in_sqlite(self, db: Database, tablename: str = "documents"):
        self.updated_at = datetime.now(tz=timezone.utc)
        db[tablename].update(self.model_dump(), where={"id": self.id})

    def table(db: Database, tablename: str = "documents"):
        return db[tablename]


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

    def save_to_sqlite(self, db: Database, table_name: str = "scan_results"):
        db[table_name].insert(self.model_dump(), pk="id", replace=True, alter=True)

    def delete_from_sqlite(self, db: Database, table_name: str = "scan_results"):
        db[table_name].delete(where={"id": self.id})

    def update_in_sqlite(self, db: Database, table_name: str = "scan_results"):
        self.updated_at = datetime.now(tz=timezone.utc)
        db[table_name].update(self.model_dump(), where={"id": self.id})

