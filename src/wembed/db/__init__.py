from typing import Tuple

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from ..config import AppConfig
from .base import Base
from .chunk_record import ChunkRecord, ChunkRecordCRUD, ChunkRecordSchema
from .document_index import DocumentIndexRecord, DocumentIndexRepo, DocumentIndexSchema
from .document_record import (
    ChunkList,
    ChunkModel,
    DocumentOut,
    DocumentRecord,
    DocumentRecordRepo,
    DocumentRecordSchema,
    StringContentOut,
)
from .file_line import FileLineRecord, FileLineRepo
from .file_record import FileLineSchema, FileRecord, FileRecordRepo, FileRecordSchema
from .input_record import InputOut, InputRecord, InputRecordRepo, InputRecordSchema
from .repo_record import RepoRecord, RepoRecordRepo, RepoRecordSchema

# Import all record models and their CRUD operations
from .scan_result import (
    ScanResult_Controller,
    ScanResultList,
    ScanResultRecord,
    ScanResultSchema,
)

from .tables import (
    IgnoreExtSchema,
    IgnoreExtTable,
    IgnorePartsSchema,
    IgnorePartsTable,
    MdXrefSchema,
    MdXrefTable,
)
from .vault_record import VaultRecord, VaultRecordRepo, VaultRecordSchema


class DBService:
    """
    Encapsulates all database connection and initialization logic.
    It is instantiated with a configuration object.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initializes the service with a database URI from the config."""
        self._db_uri = config.sqlalchemy_db_uri
        self._engine = create_engine(self._db_uri, echo=False, future=True)

    def test_connection(self) -> bool:
        """Tests if a connection to the database can be established."""
        try:
            with self._engine.connect():
                return True
        except Exception:
            return False

    def get_engine(self) -> Engine:
        """Returns the underlying SQLAlchemy Engine instance."""
        return self._engine

    def get_session(self) -> sessionmaker:
        """Returns a configured SQLAlchemy sessionmaker."""
        return sessionmaker(bind=self.get_engine(), autoflush=False)

    def initialize_tables(self, force: bool = False) -> Tuple[bool, str]:
        """
        Creates all necessary tables based on the imported models.

        Args:
            force: If True, all existing tables will be dropped before creation.

        Returns:
            A tuple containing a success boolean and a status message.
        """
        try:
            if force:
                # Drop all tables defined in the Base metadata
                Base.metadata.drop_all(self._engine)

            # Create all tables
            Base.metadata.create_all(self._engine)
            return True, "Database tables initialized successfully."
        except Exception as e:
            return False, f"An error occurred during table initialization: {e}"
