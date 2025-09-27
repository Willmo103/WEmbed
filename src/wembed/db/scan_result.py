from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, computed_field
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class ScanResultRecord(Base):
    __tablename__ = "dl_scan_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, unique=True, index=True)
    root_path: Mapped[str] = mapped_column(String, nullable=False, index=True)
    scan_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    scan_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    files: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    scan_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scan_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    user: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)


class ScanResultSchema(BaseModel):
    id: str
    root_path: str
    name: str
    scan_type: str
    files: Optional[List[str]] = None
    scan_start: datetime
    scan_end: Optional[datetime] = None
    duration: Optional[float] = None
    options: Optional[dict] = None
    user: str
    host: str

    @computed_field
    @property
    def total_files(self) -> int:
        return len(self.files) if self.files else 0

    class Config:
        from_attributes = True


class ScanResultList(BaseModel):
    results: List[ScanResultSchema]

    def add_result(self, result: ScanResultSchema):
        self.results.append(result)

    def iter_results(self):
        for result in self.results:
            yield result


class ScanResultCRUD:
    @staticmethod
    def create(db: Session, scan_result: ScanResultSchema) -> ScanResultRecord:
        db_record = ScanResultRecord(
            id=scan_result.id,
            root_path=scan_result.root_path,
            scan_type=scan_result.scan_type,
            scan_name=scan_result.name,
            files=scan_result.files,
            scan_start=scan_result.scan_start,
            scan_end=scan_result.scan_end,
            duration=(int(scan_result.duration) if scan_result.duration else None),
            options=scan_result.options,
            user=scan_result.user,
            host=scan_result.host,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, scan_id: str) -> Optional[ScanResultRecord]:
        return db.query(ScanResultRecord).filter(ScanResultRecord.id == scan_id).first()

    @staticmethod
    def get_by_root_path(db: Session, root_path: str) -> List[ScanResultRecord]:
        return (
            db.query(ScanResultRecord)
            .filter(ScanResultRecord.root_path == root_path)
            .all()
        )

    @staticmethod
    def get_by_scan_type(db: Session, scan_type: str) -> List[ScanResultRecord]:
        return (
            db.query(ScanResultRecord)
            .filter(ScanResultRecord.scan_type == scan_type)
            .all()
        )

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ScanResultRecord]:
        return db.query(ScanResultRecord).offset(skip).limit(limit).all()

    @staticmethod
    def update(
        db: Session, scan_id: str, scan_result: ScanResultSchema
    ) -> Optional[ScanResultRecord]:
        db_record = ScanResultCRUD.get_by_id(db, scan_id)
        if db_record:
            for key, value in scan_result.model_dump(exclude_unset=True).items():
                if key == "name":
                    setattr(db_record, "scan_name", value)
                elif key == "duration" and value is not None:
                    setattr(db_record, key, int(value))
                else:
                    setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, scan_id: str) -> bool:
        db_record = ScanResultCRUD.get_by_id(db, scan_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: ScanResultRecord) -> ScanResultSchema:
        return ScanResultSchema(
            id=record.id,
            root_path=record.root_path,
            name=record.scan_name or "",
            scan_type=record.scan_type,
            files=record.files,
            scan_start=record.scan_start,
            scan_end=record.scan_end,
            duration=float(record.duration) if record.duration else None,
            options=record.options,
            user=record.user,
            host=record.host,
        )
