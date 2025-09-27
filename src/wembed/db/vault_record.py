# vault_record.py

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class VaultRecord(Base):
    __tablename__ = "dl_vault"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    root_path: Mapped[str] = mapped_column(String, nullable=False)
    files: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class VaultRecordSchema(BaseModel):
    id: Optional[int] = None
    name: str
    host: str
    root_path: str
    files: Optional[List[str]] = None
    file_count: int = 0
    indexed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VaultRecordCRUD:
    @staticmethod
    def create(db: Session, vault: VaultRecordSchema) -> VaultRecord:
        db_record = VaultRecord(
            name=vault.name,
            host=vault.host,
            root_path=vault.root_path,
            files=vault.files,
            file_count=vault.file_count,
            indexed_at=vault.indexed_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, vault_id: int) -> Optional[VaultRecord]:
        return db.query(VaultRecord).filter(VaultRecord.id == vault_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[VaultRecord]:
        return db.query(VaultRecord).filter(VaultRecord.name == name).first()

    @staticmethod
    def get_by_host(db: Session, host: str) -> List[VaultRecord]:
        return db.query(VaultRecord).filter(VaultRecord.host == host).all()

    @staticmethod
    def get_by_root_path(db: Session, root_path: str) -> Optional[VaultRecord]:
        return db.query(VaultRecord).filter(VaultRecord.root_path == root_path).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[VaultRecord]:
        return db.query(VaultRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, vault_id: int, vault: VaultRecordSchema
    ) -> Optional[VaultRecord]:
        db_record = VaultRecordCRUD.get_by_id(db, vault_id)
        if db_record:
            for key, value in vault.model_dump(
                exclude_unset=True, exclude={"id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, vault_id: int) -> bool:
        db_record = VaultRecordCRUD.get_by_id(db, vault_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def update_file_count(
        db: Session, vault_id: int, file_count: int
    ) -> Optional[VaultRecord]:
        db_record = VaultRecordCRUD.get_by_id(db, vault_id)
        if db_record:
            db_record.file_count = file_count
            db_record.indexed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def to_schema(record: VaultRecord) -> VaultRecordSchema:
        return VaultRecordSchema(
            id=record.id,
            name=record.name,
            host=record.host,
            root_path=record.root_path,
            files=record.files,
            file_count=record.file_count,
            indexed_at=record.indexed_at,
        )
