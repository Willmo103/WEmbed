from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, Session
from pydantic import BaseModel, Field
from ._base import Base


class ChunkRecord(Base):
    __tablename__ = "dl_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("dl_documents.id"), nullable=False, index=True
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    text_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(datetime.timezone.utc),
    )


class ChunkRecordSchema(BaseModel):
    id: Optional[int] = None
    document_id: int
    idx: int
    text_chunk: str
    embedding: List[float]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.timezone.utc)
    )

    class Config:
        from_attributes = True


class ChunkRecordCRUD:
    @staticmethod
    def create(db: Session, chunk: ChunkRecordSchema) -> ChunkRecord:
        db_record = ChunkRecord(
            document_id=chunk.document_id,
            idx=chunk.idx,
            text_chunk=chunk.text_chunk,
            embedding=chunk.embedding,
            created_at=chunk.created_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def create_batch(db: Session, chunks: List[ChunkRecordSchema]) -> List[ChunkRecord]:
        db_records = []
        for chunk in chunks:
            db_record = ChunkRecord(
                document_id=chunk.document_id,
                idx=chunk.idx,
                text_chunk=chunk.text_chunk,
                embedding=chunk.embedding,
                created_at=chunk.created_at,
            )
            db_records.append(db_record)

        db.add_all(db_records)
        db.commit()
        for record in db_records:
            db.refresh(record)
        return db_records

    @staticmethod
    def get_by_id(db: Session, chunk_id: int) -> Optional[ChunkRecord]:
        return db.query(ChunkRecord).filter(ChunkRecord.id == chunk_id).first()

    @staticmethod
    def get_by_document_id(db: Session, document_id: int) -> List[ChunkRecord]:
        return (
            db.query(ChunkRecord)
            .filter(ChunkRecord.document_id == document_id)
            .order_by(ChunkRecord.idx)
            .all()
        )

    @staticmethod
    def get_by_document_id_and_idx(
        db: Session, document_id: int, idx: int
    ) -> Optional[ChunkRecord]:
        return (
            db.query(ChunkRecord)
            .filter(ChunkRecord.document_id == document_id, ChunkRecord.idx == idx)
            .first()
        )

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ChunkRecord]:
        return db.query(ChunkRecord).offset(skip).limit(limit).all()

    @staticmethod
    def search_by_text(db: Session, search_text: str) -> List[ChunkRecord]:
        return (
            db.query(ChunkRecord)
            .filter(ChunkRecord.text_chunk.contains(search_text))
            .all()
        )

    @staticmethod
    def update(
        db: Session, chunk_id: int, chunk: ChunkRecordSchema
    ) -> Optional[ChunkRecord]:
        db_record = ChunkRecordCRUD.get_by_id(db, chunk_id)
        if db_record:
            for key, value in chunk.model_dump(
                exclude_unset=True, exclude={"id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, chunk_id: int) -> bool:
        db_record = ChunkRecordCRUD.get_by_id(db, chunk_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_by_document_id(db: Session, document_id: int) -> int:
        deleted_count = (
            db.query(ChunkRecord)
            .filter(ChunkRecord.document_id == document_id)
            .delete()
        )
        db.commit()
        return deleted_count

    @staticmethod
    def to_schema(record: ChunkRecord) -> ChunkRecordSchema:
        return ChunkRecordSchema(
            id=record.id,
            document_id=record.document_id,
            idx=record.idx,
            text_chunk=record.text_chunk,
            embedding=record.embedding,
            created_at=record.created_at,
        )
