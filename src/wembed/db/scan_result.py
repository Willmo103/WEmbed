from datetime import datetime
from typing import List, Optional, Generator, Type

from pydantic import BaseModel, computed_field
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class ScanResultRecord(Base):
    """
    SQLAlchemy model for scan results.

    Attributes:
    - id (str): Unique identifier for the scan result.
    - root_path (str): The root path that was scanned.
    - scan_type (str): The type of scan performed (e.g., 'full', 'incremental').
    - scan_name (Optional[str]): An optional name for the scan.
    - files (Optional[List[str]]): List of file paths found during the scan.
    - scan_start (datetime): Timestamp when the scan started.
    - scan_end (Optional[datetime]): Timestamp when the scan ended.
    - duration (Optional[int]): Duration of the scan in seconds.
    - options (Optional[dict]): Additional options used during the scan.
    - user (str): The user who initiated the scan.
    - host (str): The host where the scan was performed.
    """
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
    def total_files(self) -> int:
        """Compute the total number of files in the scan result."""
        return len(self.files) if self.files else 0

    class Config:
        """Pydantic configuration to allow ORM mode."""
        from_attributes = True


class ScanResultList(BaseModel):
    results: List[ScanResultSchema]

    def add_result(self, result: ScanResultSchema) -> None:
        """
        Add a scan result to the list.
        Args:
            result (ScanResultSchema): The scan result to add.

        Returns:
            None
        """
        self.results.append(result)

    def iter_results(self) -> Generator[ScanResultSchema, None, None]:
        """
        Generator to iterate over scan results.

        Returns:
            Generator[ScanResultSchema, None, None]: A generator of scan results.
        """
        for result in self.results:
            yield result


class ScanResult_Controller:
    """
    A Controller class to handle CRUD operations for ScanResultRecord.

    Methods:
    - create: Create a new scan result record.
    - get_by_id: Fetch a scan result by its ID.
    - get_by_root_path: Fetch scan results by their root path.
    - get_by_scan_type: Fetch scan results by their scan type.
    - get_all: Fetch all scan results with pagination.
    - update: Update a scan result by its ID.
    - delete: Delete a scan result by its ID.
    - to_schema: Convert a ScanResultRecord to a ScanResultSchema.
    """
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
        """
        Fetch a scan result by its ID.
        Args:
            db (Session): The database session.
            scan_id (str): The ID of the scan result to fetch.
        Returns:
            Optional[ScanResultRecord]: The scan result record, or None if not found.
        """
        return db.query(ScanResultRecord).filter(ScanResultRecord.id == scan_id).first()

    @staticmethod
    def get_by_root_path(db: Session, root_path: str) -> list[ScanResultSchema]:
        """
        Fetch scan results by their root path.
        Args:
            db (Session): The database session.
            root_path (str): The root path to filter by.

        Returns:
            List[ScanResultSchema]: A list of scan result schemas.
        """
        results = (
            db.query(ScanResultRecord)
            .filter(ScanResultRecord.root_path == root_path)
            .all()
        )
        try:
            records = [ScanResultRecord(**r.__dict__) for r in results]
            return (
                [ScanResult_Controller.to_schema(record) for record in records]
                if results
                else []
            )
        except Exception:
            return []

    @staticmethod
    def get_by_scan_type(db: Session, scan_type: str) -> List[ScanResultSchema]:
        """
        Fetch scan results by their scan type.
        Args:
            db (Session): The database session.
            scan_type (str): The type of scan to filter by.

        Returns:
            List[ScanResultSchema]: A list of scan result schemas.
        """
        results = db.query(
            ScanResultRecord,
            db.query(ScanResultRecord)
            .filter(ScanResultRecord.scan_type == scan_type)
            .all(),
        )
        try:
            return (
                [ScanResult_Controller.to_schema(record[0]) for record in results]
                if results
                else []
            )
        except Exception:
            return []

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[ScanResultSchema]:
        """
        Fetch all scan results with pagination.
        Args:
            db (Session): The database session.
            skip (int) = 0: Number of records to skip for pagination.
            limit (int) = 100: Maximum number of records to return.

        Returns:
            List[ScanResultSchema]: A list of scan result schemas.
        """
        results = db.query(ScanResultRecord).offset(skip).limit(limit).all()
        try:
            records = [ScanResultRecord(**r.__dict__) for r in results]
            return (
                [ScanResult_Controller.to_schema(record) for record in records]
                if results
                else []
            )
        except Exception:
            return []

    @staticmethod
    def update(
        db: Session, scan_id: str, scan_result: ScanResultSchema
    ) -> Optional[ScanResultRecord]:
        """
        Update a scan result by its ID.
        Args:
            db (Session): The database session.
            scan_id (str): The ID of the scan result to update.
            scan_result (ScanResultSchema): The updated scan result data.
        Returns:
            Optional[ScanResultRecord]: The updated scan result record, or None if not found.
        """
        db_record = ScanResult_Controller.get_by_id(db, scan_id)
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
        """
        Delete a scan result by its ID.

        Args:
            db (Session): The database session.
            scan_id (str): The ID of the scan result to delete.

        Returns:
            bool: True if the record was deleted, False if not found.
        """
        db_record = ScanResult_Controller.get_by_id(db, scan_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def to_schema(record: ScanResultRecord) -> ScanResultSchema:
        """
        Convert a ScanResultRecord to a ScanResultSchema.

        Args:
            record (ScanResultRecord): The database record to convert.

        Returns:
            ScanResultSchema: A pydantic schema representation of the record.
        """
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
