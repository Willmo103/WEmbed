"""
SQLAlchemy models and Pydantic schemas for file lines, along with Repository classes for CRUD operations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .base import Base


class FileLineRecord(Base):
    """
    SQLAlchemy model for a line in a file, including its embedding.

    Attributes:
        id (int): Primary key.
        file_id (str): Foreign key to the associated file.
        file_repo_name (str): Name of the repository the file belongs to.
        file_repo_type (str): Type of the repository (e.g., git, svn).
        line_number (int): Line number in the file.
        line_text (str): Text content of the line.
        embedding (Optional[List[float]]): Embedding vector for the line.
        created_at (datetime): Timestamp of when the record was created.
    """

    __tablename__ = "dl_filelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(
        ForeignKey("dl_files.id"), nullable=False, index=True
    )
    file_repo_name: Mapped[str] = mapped_column(String, nullable=False)
    file_repo_type: Mapped[str] = mapped_column(String, nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    line_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class FileLineSchema(BaseModel):
    id: Optional[int] = Field(None, description="Unique identifier for the file line")
    file_id: str = Field(..., max_length=50, description="PK id of the associated file")
    file_repo_name: str = Field(..., max_length=100, description="Name of the repository the file belongs to")
    file_repo_type: str = Field(..., max_length=50, description="Type of the repository (e.g., git, svn)")
    file_version: str = Field(..., max_length=50, description="Version of the file")
    line_number: int = Field(..., description="Line number in the file")
    line_text: str = Field(..., description="Text content of the line")
    embedding: Optional[List[float]] = Field(None, description="Embedding vector for the line")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the record was created")

    @computed_field
    @property
    def composite_id(self) -> str:
        return f"{self.file_id}:{self.line_number}"

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FileLineRepo:
    """
    Repository class for managing FileLineRecord entries in the database.
    Provides methods for CRUD operations and various queries.

    Methods:
        create: Create a new file line record.
        create_batch: Create multiple file line records in a batch.
        get_by_id: Retrieve a file line record by its ID.
        get_by_file_id: Retrieve all lines for a specific file ID.
        get_by_file_and_line: Retrieve a specific line in a file by file ID and line number.
        get_by_repo_name: Retrieve all lines from files in a specific repository.
        get_by_repo_type: Retrieve all lines from files in a specific repository type.
        search_by_text: Search for lines containing specific text.
        get_lines_with_embeddings: Retrieve all lines that have embeddings.
        get_lines_without_embeddings: Retrieve all lines that do not have embeddings.
        get_all: Retrieve all file line records with pagination.
        update: Update an existing file line record.
        update_embedding: Update the embedding for a specific line in a file.
        delete: Delete a file line record by its ID.
        delete_by_file_id: Delete all lines associated with a specific file ID.
        delete_by_file_and_line: Delete a specific line in a file by file ID and line number.
        get_line_count_by_file: Get the count of lines for a specific file ID.
        to_schema: Convert a FileLineRecord to a FileLineSchema.
    """

    @staticmethod
    def create(db: Session, file_line: FileLineSchema) -> FileLineRecord:
        db_record = FileLineRecord(
            file_id=file_line.file_id,
            file_repo_name=file_line.file_repo_name,
            file_repo_type=file_line.file_repo_type,
            line_number=file_line.line_number,
            line_text=file_line.line_text,
            embedding=file_line.embedding,
            created_at=file_line.created_at,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        return db_record

    @staticmethod
    def create_batch(
        db: Session, file_lines: List[FileLineSchema]
    ) -> List[FileLineRecord]:
        """
        Create multiple file line records in a batch.

        Args:
            db (Session): SQLAlchemy session object.
            file_lines (List[FileLineSchema]): List of FileLineSchema objects to be added

        Returns:
            List[FileLineSchema]: List of created FileLineRecord objects.
        """
        db_records = []
        for file_line in file_lines:
            db_record = FileLineRecord(
                file_id=file_line.file_id,
                file_repo_name=file_line.file_repo_name,
                file_repo_type=file_line.file_repo_type,
                line_number=file_line.line_number,
                line_text=file_line.line_text,
                embedding=file_line.embedding,
                created_at=file_line.created_at,
            )
            db_records.append(db_record)

        db.add_all(db_records)
        db.commit()
        for record in db_records:
            db.refresh(record)
            record = FileLineSchema(**record.__dict__)
        return db_records

    @staticmethod
    def get_by_id(db: Session, line_id: int) -> Optional[FileLineRecord]:
        """
        Get a file line record by its ID.
        Args:
            db (Session): SQLAlchemy session object.
            line_id (int): ID of the file line record.
        Returns:
            Optional[FileLineRecord]: The file line record if found, else None.
        """
        return db.query(FileLineRecord).filter(FileLineRecord.id == line_id).first()

    @staticmethod
    def get_by_file_id(db: Session, file_id: str) -> List[FileLineRecord]:
        """
        Get all file line records for a specific file ID.
        Args:
            db (Session): SQLAlchemy session object.
            file_id (str): ID of the file.
        Returns:
            List[FileLineRecord]: List of file line records for the specified file ID.
        """
        return (
            db.query(FileLineRecord)
            .filter(FileLineRecord.file_id == file_id)
            .order_by(FileLineRecord.line_number)
            .all()
        )

    @staticmethod
    def get_by_file_and_line(
        db: Session, file_id: str, line_number: int
    ) -> Optional[FileLineRecord]:
        """
        Get a specific file line record by file ID and line number.

        Args:
            db (Session): SQLAlchemy session object.
            file_id (str): ID of the file.
            line_number (int): Line number in the file.
        Returns:
            Optional[FileLineRecord]: The file line record if found, else None.
        """
        return (
            db.query(FileLineRecord)
            .filter(
                FileLineRecord.file_id == file_id,
                FileLineRecord.line_number == line_number,
            )
            .first()
        )

    @staticmethod
    def get_by_repo_name(db: Session, repo_name: str) -> List[FileLineSchema]:
        """
        Get all file line records for a specific repository name.

        Args:
            db (Session): SQLAlchemy session object.
            repo_name (str): Name of the repository.

        Returns:
            List[FileLineSchema]: List of file line records for the specified repository name.
        """
        results = (
            db.query(FileLineRecord)
            .filter(FileLineRecord.file_repo_name == repo_name)
            .all()
        )
        records = [FileLineRecord(**r.__dict__) for r in results]
        return [FileLineRepo.to_schema(r) for r in records]

    @staticmethod
    def get_by_repo_type(db: Session, repo_type: str) -> List[FileLineSchema]:
        """
        Get all file line records for a specific repository type.

        Args:
            db (Session): SQLAlchemy session object.
            repo_type (str): Type of the repository (e.g., git, svn).

        Returns:
            List[FileLineSchema]: List of file line records for the specified repository type.
        """
        results = (
            db.query(FileLineRecord)
            .filter(FileLineRecord.file_repo_type == repo_type)
            .all()
        )
        records = [FileLineRecord(**r.__dict__) for r in results]
        return [FileLineRepo.to_schema(r) for r in records]

    @staticmethod
    def search_by_text(db: Session, search_text: str) -> List[FileLineSchema]:
        """
        Search for file line records containing specific text.
        Args:
            db (Session): SQLAlchemy session object.
            search_text (str): Text to search for within line_text.

        Returns:
            List[FileLineSchema]: List of file line records containing the search text.
        """
        results = (
            db.query(FileLineRecord)
            .filter(FileLineRecord.line_text.contains(search_text))
            .all()
        )
        records = [FileLineRecord(**r.__dict__) for r in results]
        return [FileLineRepo.to_schema(r) for r in records]

    @staticmethod
    def get_lines_with_embeddings(db: Session) -> List[FileLineSchema]:
        """
        Get all file line records with embeddings.
        Args:
            db (Session): SQLAlchemy session object.

        Returns:
            List[FileLineSchema]: List of file line records with embeddings.
        """
        results = (
            db.query(FileLineRecord).filter(FileLineRecord.embedding.is_not(None)).all()
        )
        records = [FileLineRecord(**r.__dict__) for r in results]
        return [FileLineRepo.to_schema(r) for r in records]

    @staticmethod
    def get_lines_without_embeddings(db: Session) -> List[FileLineSchema]:
        """
        Get all file line records without embeddings.

        Args:
            db (Session): SQLAlchemy session object.

        Returns:
            List[FileLineSchema]: List of file line records without embeddings.
        """
        results = (
            db.query(FileLineRecord).filter(FileLineRecord.embedding.is_(None)).all()
        )
        records = [FileLineRecord(**r.__dict__) for r in results]
        return [FileLineRepo.to_schema(r) for r in records]

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[FileLineSchema]:
        """
        Get all file line records with pagination.

        Args:
            db (Session): SQLAlchemy session object.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[FileLineSchema]: List of file line records.
        """
        results = db.query(FileLineRecord).offset(skip).limit(limit).all()
        records = [FileLineRecord(**r.__dict__) for r in results]
        return [FileLineRepo.to_schema(r) for r in records]

    @staticmethod
    def update(
        db: Session, line_id: int, file_line: FileLineSchema
    ) -> Optional[FileLineRecord]:
        """
        Update an existing file line record.

        Args:
            db (Session): SQLAlchemy session object.
            line_id (int): ID of the file line record.
            file_line (FileLineSchema): Updated file line data.

        Returns:
            Optional[FileLineRecord]: The updated file line record if found, else None.
        """
        db_record = FileLineRepo.get_by_id(db, line_id)
        if db_record:
            for key, value in file_line.model_dump(
                exclude_unset=True, exclude={"id", "composite_id"}
            ).items():
                setattr(db_record, key, value)
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def update_embedding(
        db: Session, file_id: str, line_number: int, embedding: List[float]
    ) -> Optional[FileLineRecord]:
        """
        Update the embedding for a specific line in a file.

        Args:
            db (Session): SQLAlchemy session object.
            file_id (str): ID of the file.
            line_number (int): Line number in the file.
            embedding (List[float]): New embedding vector.
        Returns:
            Optional[FileLineRecord]: The updated file line record if found, else None.
        """
        db_record = FileLineRepo.get_by_file_and_line(db, file_id, line_number)
        if db_record:
            db_record.embedding = embedding
            db.commit()
            db.refresh(db_record)
        return db_record

    @staticmethod
    def delete(db: Session, line_id: int) -> bool:
        """
        Delete a file line record by its ID.

        Args:
            db (Session): SQLAlchemy session object.
            line_id (int): ID of the file line record.

        Returns:
            bool: True if the record was found and deleted, else False.
        """
        db_record = FileLineRepo.get_by_id(db, line_id)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_by_file_id(db: Session, file_id: str) -> int:
        """
        Delete all lines associated with a specific file ID.

        Args:
            db (Session): SQLAlchemy session object.
            file_id (str): ID of the file.

        Returns:
            int: The number of deleted lines.
        """
        deleted_count = (
            db.query(FileLineRecord).filter(FileLineRecord.file_id == file_id).delete()
        )
        db.commit()
        return deleted_count

    @staticmethod
    def delete_by_file_and_line(db: Session, file_id: str, line_number: int) -> bool:
        """
        Delete a specific line in a file by file ID and line number.

        Args:
            db (Session): SQLAlchemy session object.
            file_id (str): ID of the file.
            line_number (int): Line number in the file.

        Returns:
            bool: True if the record was found and deleted, else False.
        """
        db_record = FileLineRepo.get_by_file_and_line(db, file_id, line_number)
        if db_record:
            db.delete(db_record)
            db.commit()
            return True
        return False

    @staticmethod
    def get_line_count_by_file(db: Session, file_id: str) -> int:
        """
        Get the count of lines for a specific file ID.

        Args:
            db (Session): SQLAlchemy session object.
            file_id (str): ID of the file.
        Returns:
            int: The count of lines for the specified file ID.
        """
        return (
            db.query(FileLineRecord).filter(FileLineRecord.file_id == file_id).count()
        )

    @staticmethod
    def to_schema(record: FileLineRecord) -> FileLineSchema:
        """
        Convert a FileLineRecord to a FileLineSchema.

        Args:
            record (FileLineRecord): The FileLineRecord instance to convert.

        Returns:
            FileLineSchema: The corresponding FileLineSchema instance.
        """
        return FileLineSchema(
            id=record.id,
            file_id=record.file_id,
            file_repo_name=record.file_repo_name,
            file_repo_type=record.file_repo_type,
            file_version="1",  # Default version since it's not in the record
            line_number=record.line_number,
            line_text=record.line_text,
            embedding=record.embedding,
            created_at=record.created_at,
        )
