from pathlib import Path

import psycopg2
import typer
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from ..config import AppConfig as app_config  # noqa
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

# from .tables import (
#     IgnoreExtSchema,
#     IgnoreExtTable,
#     IgnorePartsSchema,
#     IgnorePartsTable,
#     MdXrefSchema,
#     MdXrefTable,
# )
from .vault_record import VaultRecord, VaultRecordCRUD, VaultRecordSchema

# Database initialization and connection management
DB_INIT = False
_db_uri = app_config.sqlalchemy_db_uri


def test_db_connection() -> bool:
    try:
        if _db_uri.startswith("postgresql"):
            conn = psycopg2.connect(
                dbname=app_config.pg_db,
                user=app_config.pg_user,
                password=app_config.pg_password,
                host=app_config.pg_host,
                port=app_config.pg_port,
            )
            conn.close()
            return True
        elif _db_uri.startswith("sqlite"):
            # For SQLite, just check if the file can be accessed/created
            db_path = _db_uri.replace("sqlite:///", "")
            Path(db_path).touch(exist_ok=True)
            return True
        else:
            return False
    except Exception:
        return False


def _get_engine() -> Engine:
    return create_engine(_db_uri, echo=False, future=True)


def drop_models() -> None:
    eng = _get_engine()
    sql = "DELETE FROM interface WHERE table_name Like 'dl_%';"
    with eng.connect() as conn:
        conn.execute(text(sql))


def _init_db(force: bool = False) -> tuple[bool, str] | None:
    global DB_INIT
    if not DB_INIT or force:
        try:
            if force:
                try:
                    drop_models()
                except Exception:
                    pass
            success, msg = create_models()
            if success:
                DB_INIT = True
            return success, msg
        except Exception as e:
            return False, f"Error initializing database: {e}"


def create_models() -> tuple[bool, str]:
    global DB_INIT
    try:
        # Create all tables using the Base metadata
        Base.metadata.create_all(_get_engine())
        DB_INIT = True
        return True, "Database models created successfully."
    except Exception as e:
        return False, str(e) or "No error message available."


def get_session() -> sessionmaker:
    """
    Get a SQLAlchemy sessionmaker for the configured database.

    Returns:
        sessionmaker: A configured SQLAlchemy sessionmaker instance.
    """
    return sessionmaker(bind=_get_engine(), autoflush=False)


# CLI Commands
db_cli = typer.Typer(name="db", no_args_is_help=True, help="Database commands")


@db_cli.command(name="test-db", help="Test Postgres DB connection")
def is_db_conn():
    if test_db_connection():
        print("Postgres DB connection successful.")
    else:
        print("Postgres DB connection failed.")


@db_cli.command(name="init", help="Initialize the database")
def init_db_command(
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-initialization of the database"
    ),
) -> None:
    success, msg = False, ""
    try:
        typer.echo("Initializing database...")
        success, msg = _init_db(force)
        if not success:
            typer.echo(f"Error initializing database: {msg}")
        else:
            typer.echo(msg or "Database initialized successfully.")
    except Exception as e:
        typer.echo(f"Error initializing database: {e}")
    if not success:
        raise typer.Exit(code=1)


# Export all models, schemas, and CRUD operations for easy importing
__all__ = [
    # Database management functions
    "test_db_connection",
    "create_models",
    "get_session",
    "get_session_local",
    "get_session_remote",
    "db_cli",
    # Scan Result
    "ScanResultRecord",
    "ScanResultSchema",
    "ScanResultList",
    "ScanResult_Controller",
    # Vault Record
    "VaultRecord",
    "VaultRecordSchema",
    "VaultRecordCRUD",
    # Repo Record
    "RepoRecord",
    "RepoRecordSchema",
    "RepoRecordRepo",
    # Document Index
    "DocumentIndexRecord",
    "DocumentIndexSchema",
    "DocumentIndexRepo",
    # Input Record
    "InputRecord",
    "InputRecordSchema",
    "InputOut",
    "InputRecordRepo",
    # Chunk Record
    "ChunkRecord",
    "ChunkRecordSchema",
    "ChunkRecordCRUD",
    # File Record
    "FileRecord",
    "FileRecordSchema",
    "FileLineSchema",
    "FileRecordRepo",
    # Document Record
    "DocumentRecord",
    "DocumentRecordSchema",
    "ChunkModel",
    "ChunkList",
    "DocumentOut",
    "StringContentOut",
    "DocumentRecordRepo",
    # File Line
    "FileLineRecord",
    "FileLineSchema",
    "FileLineRepo",
]
