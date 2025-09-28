# vault_record.py

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class VaultRecord(Base):
    """
    Represents a vault in the database.

    Attributes:
     - id (int): Primary key.
     - name (str): Name of the vault.
     - host (str): Host of the vault (e.g., GitHub, GitLab).
     - root_path (str): Root path of the vault.
     - files (List[str], optional): List of file paths in the vault.
     - file_count (int): Number of files in the vault.
     - indexed_at (datetime, optional): Timestamp of the last indexing operation.
    """
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
        """Pydantic configuration for ORM compatibility."""
        from_attributes = True


class VaultRecordRepo:
    """
    Repository class for managing VaultRecord database operations.
    Provides methods for creating, reading, updating, and deleting vault records.
    """
    @staticmethod
    def create(db: Session, vault: VaultRecordSchema) -> VaultRecord:
        """
        Create a new vault record in the database.

        Args:
            db (Session): The database session.
            vault (VaultRecordSchema): The vault data to create.
        Returns:
            VaultRecord: The created vault record.
        """
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
        """
        Retrieve a vault record by its ID.
        Args:
            db (Session): The database session.
            vault_id (int): The ID of the vault to retrieve.

        Returns:
            Optional[VaultRecord]: The retrieved vault record, or None if not found.
        """
        return db.query(VaultRecord).filter(VaultRecord.id == vault_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[VaultRecord]:
        """
        Retrieve a vault record by its name.
        Args:
            db (Session): The database session.
            name (str): The name of the vault to retrieve.

        Returns:
            Optional[VaultRecord]: The retrieved vault record, or None if not found.
        """
        return db.query(VaultRecord).filter(VaultRecord.name == name).first()

    @staticmethod
    def get_by_host(db: Session, host: str) -> List[VaultRecordSchema]:
        """
        Retrieve vault records by their host.
        Args:
            db (Session): The database session.
            host (str): The host of the vaults to retrieve.

        Returns:
            List[VaultRecordSchema]: The retrieved vault records.
        """
        results = db.query(VaultRecord).filter(VaultRecord.host == host).all()
        try:
            records = [VaultRecord(**r.__dict__) for r in results]
            return [VaultRecordRepo.to_schema(r) for r in records]
        except Exception:
            # Handle exceptions or log errors as needed
            return []

    @staticmethod
    def get_by_root_path(db: Session, root_path: str) -> Optional[VaultRecord]:
        """
        Retrieve a vault record by its root path.
        Args:
            db (Session): The database session.
            root_path (str): The root path of the vault to retrieve.

        Returns:
            Optional[VaultRecord]: The retrieved vault record, or None if not found.
        """
        return db.query(VaultRecord).filter(VaultRecord.root_path == root_path).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[VaultRecordSchema]:
        """
        Retrieve all vault records with pagination.
        Args:
            db (Session): The database session.
            skip (int): The number of records to skip (for pagination).
            limit (int): The maximum number of records to retrieve.

        Returns:
            List[VaultRecord]: The retrieved vault records.
        """
        retsults = db.query(VaultRecord).offset(skip).limit(limit).all()
        try:
            records = [VaultRecord(**r.__dict__) for r in retsults]
            return [VaultRecordRepo.to_schema(r) for r in records]
        except Exception:
            # Handle exceptions or log errors as needed
            return []

    @staticmethod
    def update(
        db: Session, vault_id: int, vault: VaultRecordSchema
    ) -> Optional[VaultRecord]:
        """Update an existing vault record in the database.
        Args:
            db (Session): The database session.
            vault_id (int): The ID of the vault to update.
            vault (VaultRecordSchema): The updated vault data.
        Returns:
            Optional[VaultRecord]: The updated vault record, or None if not found.
        """
        db_record = VaultRecordRepo.get_by_id(db, vault_id)
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
        """Delete a vault record from the database by its ID.
        Args:
            db (Session): The database session.
            vault_id (int): The ID of the vault to delete.
        Returns:
            bool: True if the record was deleted, False if not found.
        """
        db_record = VaultRecordRepo.get_by_id(db, vault_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def update_file_count(
        db: Session, vault_id: int, file_count: int
    ) -> Optional[VaultRecord]:
        """
        Update the file count and indexed_at timestamp of a vault record.
        Args:
            db (Session): The database session.
            vault_id (int): The ID of the vault to update.
            file_count (int): The new file count to set.
        Returns:
            Optional[VaultRecord]: The updated vault record, or None if not found.
        """
        db_record = VaultRecordRepo.get_by_id(db, vault_id)
        if db_record:
            db_record.file_count = file_count
            db_record.indexed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def to_schema(record: VaultRecord) -> VaultRecordSchema:
        """
        Convert a VaultRecord to a VaultRecordSchema.
        Args:
            record (VaultRecord): The vault record to convert.

        Returns:
            VaultRecordSchema: The converted vault record schema.
        """
        return VaultRecordSchema(
            id=record.id,
            name=record.name,
            host=record.host,
            root_path=record.root_path,
            files=record.files,
            file_count=record.file_count,
            indexed_at=record.indexed_at,
        )
