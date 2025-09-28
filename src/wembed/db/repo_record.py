# repo_record.py

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class RepoRecord(Base):
    """
    Represents a code repository in the database.

    Attributes:
        id (int): Primary key.
        name (str): Name of the repository.
        host (str): Host of the repository (e.g., GitHub, GitLab).
        root_path (str): Root path of the repository.
        files (List[str], optional): List of file paths in the repository.
        file_count (int): Number of files in the repository.
        indexed_at (datetime, optional): Timestamp of the last indexing operation.
    """

    __tablename__ = "dl_repo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    host: Mapped[str] = mapped_column(String, nullable=False)
    root_path: Mapped[str] = mapped_column(String, nullable=False)
    files: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RepoRecordSchema(BaseModel):
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


class RepoRecordRepo:
    """
    Repository class for managing RepoRecord database operations.
    Provides methods for creating, reading, updating, and deleting repository records.
    """

    @staticmethod
    def create(db: Session, repo: RepoRecordSchema) -> RepoRecord:
        """
        Creates a new RepoRecord in the database.

        Args:
            db (Session): SQLAlchemy session object.
            repo (RepoRecordSchema): Schema object containing repository details.

        Returns:
            RepoRecord: The created RepoRecord object.
        """
        db_record = RepoRecord(
            name=repo.name,
            host=repo.host,
            root_path=repo.root_path,
            files=repo.files,
            file_count=repo.file_count,
            indexed_at=repo.indexed_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def get_by_id(db: Session, repo_id: int) -> Optional[RepoRecord]:
        """
        Retrieves a RepoRecord by its ID.

        Args:
            db (Session): SQLAlchemy session object.
            repo_id (int): ID of the repository to retrieve.

        Returns:
            Optional[RepoRecord]: The retrieved RepoRecord object, or None if not found.
        """
        return db.query(RepoRecord).filter(RepoRecord.id == repo_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[RepoRecord]:
        """
        Retrieves a RepoRecord by its name.

        Args:
            db (Session): SQLAlchemy session object.
            name (str): Name of the repository to retrieve.

        Returns:
            Optional[RepoRecord]: The retrieved RepoRecord object, or None if not found.
        """
        return db.query(RepoRecord).filter(RepoRecord.name == name).first()

    @staticmethod
    def get_by_host(db: Session, host: str) -> List[RepoRecordSchema]:
        """
        Retrieves all RepoRecords by their host.

        Args:
            db (Session): SQLAlchemy session object.
            host (str): Host of the repositories to retrieve.

        Returns:
            List[RepoRecord]: List of RepoRecord objects matching the host.
        """
        results = db.query(RepoRecord).filter(RepoRecord.host == host).all()
        try:
            records = [RepoRecord(**r.__dict__) for r in results]
            return [RepoRecordSchema(**r.__dict__) for r in records]
        except Exception as e:
            print(f"Error retrieving records by host {host}: {e}")
            return []

    @staticmethod
    def get_by_root_path(db: Session, root_path: str) -> Optional[RepoRecord]:
        """
        Retrieves a RepoRecord by its root path.

        Args:
            db (Session): SQLAlchemy session object.
            root_path (str): Root path of the repository to retrieve.

        Returns:
            Optional[RepoRecord]: The retrieved RepoRecord object, or None if not found.
        """
        return db.query(RepoRecord).filter(RepoRecord.root_path == root_path).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[RepoRecordSchema]:
        """
        Retrieves all RepoRecords with pagination.

        Args:
            db (Session): SQLAlchemy session object.
            skip (int): Number of records to skip for pagination.
            limit (int): Maximum number of records to return.

        Returns:
            List[RepoRecord]: List of RepoRecord objects.
        """
        results = db.query(RepoRecord).offset(skip).limit(limit).all()
        try:
            records = [RepoRecord(**r.__dict__) for r in results]
            return [RepoRecordSchema(**r.__dict__) for r in records]
        except Exception as e:
            print(f"Error retrieving all records: {e}")
            return []

    @staticmethod
    def update(
        db: Session, repo_id: int, repo: RepoRecordSchema
    ) -> Optional[RepoRecord]:
        """
        Updates an existing RepoRecord in the database.

        Args:
            db (Session): SQLAlchemy session object.
            repo_id (int): ID of the repository to update.
            repo (RepoRecordSchema): Schema object containing updated repository details.

        Returns:
            Optional[RepoRecord]: The updated RepoRecord object, or None if not found.
        """
        db_record = RepoRecordRepo.get_by_id(db, repo_id)
        if db_record:
            for key, value in repo.model_dump(
                exclude_unset=True, exclude={"id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, repo_id: int) -> bool:
        """
        Deletes a RepoRecord from the database by its ID.

        Args:
            db (Session): SQLAlchemy session object.
            repo_id (int): ID of the repository to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        db_record = RepoRecordRepo.get_by_id(db, repo_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def update_file_count(
        db: Session, repo_id: int, file_count: int
    ) -> Optional[RepoRecord]:
        """
        Updates the file count and indexed_at timestamp of a RepoRecord.

        Args:
            db (Session): SQLAlchemy session object.
            repo_id (int): ID of the repository to update.
            file_count (int): New file count to set.

        Returns:
            Optional[RepoRecord]: The updated RepoRecord object, or None if not found.
        """
        db_record = RepoRecordRepo.get_by_id(db, repo_id)
        if db_record:
            db_record.file_count = file_count
            db_record.indexed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def to_schema(record: RepoRecord) -> RepoRecordSchema:
        """
        Converts a RepoRecord ORM object to its corresponding Pydantic schema.

        Args:
            record (RepoRecord): The RepoRecord ORM object to convert.

        Returns:
            RepoRecordSchema: The corresponding Pydantic schema object.
        """
        return RepoRecordSchema(
            id=record.id,
            name=record.name,
            host=record.host,
            root_path=record.root_path,
            files=record.files,
            file_count=record.file_count,
            indexed_at=record.indexed_at,
        )
