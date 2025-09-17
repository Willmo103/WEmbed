# db/__init__.py

from pathlib import Path
import psycopg2
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import Session, sessionmaker
from ._base import Base
from config import app_config
import typer

# Import all record models and their CRUD operations
from .scan_result import (
    ScanResultRecord,
    ScanResultSchema,
    ScanResultList,
    ScanResultCRUD,
)
from .vault_record import VaultRecord, VaultRecordSchema, VaultRecordCRUD
from .repo_record import RepoRecord, RepoRecordSchema, RepoRecordCRUD
from .document_index import (
    DocumentIndexRecord,
    DocumentIndexSchema,
    DocumentIndexCRUD,
)
from .input_record import (
    InputRecord,
    InputRecordSchema,
    InputOut,
    InputRecordCRUD,
)
from .chunk_record import ChunkRecord, ChunkRecordSchema, ChunkRecordCRUD
from .file_record import (
    FileRecord,
    FileRecordSchema,
    FileLineSchema,
    FileRecordCRUD,
)
from .document_record import (
    DocumentRecord,
    DocumentRecordSchema,
    ChunkModel,
    ChunkList,
    DocumentOut,
    StringContentOut,
    DocumentRecordCRUD,
)
from .file_line import FileLineRecord, FileLineSchema, FileLineCRUD


# Database initialization and connection management
DB_INIT = False
_local_uri = app_config.local_db_uri
_remote_uri = app_config.remote_db_uri


def test_db_connection() -> bool:
    sql = "SELECT schema_name FROM information_schema.schemata"
    try:
        eng = create_engine(_remote_uri)
        with eng.connect() as conn:
            conn.execute(text(sql))
            return True
    except psycopg2.Error:
        return False


def _get_engine(uri: str) -> Engine:
    return create_engine(uri)


def drop_models(uri: str) -> None:
    eng = _get_engine(uri)
    sql = "DELETE FROM interface WHERE table_name Like 'dl_%';"
    with eng.connect() as conn:
        conn.execute(text(sql))


def _init_db(uri: str, force: bool = False) -> tuple[bool, str]:
    global DB_INIT
    if not DB_INIT or force:
        try:
            if force:
                try:
                    drop_models(uri)
                except Exception:
                    pass
            success, msg = create_models(uri)
            if success:
                DB_INIT = True
            return success, msg
        except Exception as e:
            return False, f"Error initializing database: {e}"


def create_models(uri: str) -> tuple[bool, str]:
    global DB_INIT
    try:
        # Create all tables using the Base metadata
        Base.metadata.create_all(_get_engine(uri))
        DB_INIT = True
        return True, "Database models created successfully."
    except Exception as e:
        return False, str(e) or "No error message available."


def get_session_local(uri: str = _local_uri) -> Session:
    sesh: Session = sessionmaker(
        autocommit=False, autoflush=False, bind=_get_engine(uri)
    )()
    return sesh


def get_session_remote(uri: str = _remote_uri) -> Session | None:
    try:
        return sessionmaker(
            autocommit=False, autoflush=False, bind=_get_engine(uri)
        )()
    except Exception:
        return None


def get_session() -> Session:
    return get_session_remote() or get_session_local()


# CLI Commands
db_cli = typer.Typer(name="db", no_args_is_help=True, help="Database commands")


@db_cli.command(name="test-db", help="Test Postgres DB connection")
def test_db_command():
    if test_db_connection():
        print("Postgres DB connection successful.")
    else:
        print("Postgres DB connection failed.")


@db_cli.command(name="init", help="Initialize the database")
def init_db_command(
    remote: bool = typer.Option(
        False, "--remote", "-r", help="Initialize remote Postgres database"
    ),
    local: bool = typer.Option(
        False, "--local", "-l", help="Initialize local SQLite database"
    ),
    test: bool = typer.Option(
        False,
        "--test",
        "-t",
        help="Initialize a test sqlite database at `.\\test_db.db`",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-initialization of the database"
    ),
) -> None:
    success, msg = False, ""
    if remote:
        try:
            typer.echo("Initializing remote Postgres database...")
            success, msg = _init_db(_remote_uri, force)
            if not success:
                typer.echo(
                    f"Error initializing remote Postgres database: {msg}"
                )
            else:
                typer.echo(
                    msg or "Remote Postgres database initialized successfully."
                )
        except Exception as e:
            typer.echo(f"Error initializing remote Postgres database: {e}")
    if local:
        try:
            typer.echo("Initializing local SQLite database...")
            success, msg = _init_db(_local_uri, force)
            if not success:
                typer.echo(f"Error initializing local SQLite database: {msg}")
            else:
                typer.echo(
                    msg or "Local SQLite database initialized successfully."
                )
        except Exception as e:
            typer.echo(f"Error initializing local SQLite database: {e}")
    if test:
        if Path(app_config.app_storage).joinpath("test_db.db").exists():
            Path(app_config.app_storage).joinpath("test_db.db").unlink()
        try:
            typer.echo("Initializing test SQLite database...")
            success, msg = _init_db(
                "sqlite:///"
                + str(Path(app_config.app_storage).joinpath("test_db.db")),
                force=True,
            )
            if not success:
                typer.echo(f"Error initializing test SQLite database: {msg}")
            else:
                typer.echo(
                    msg or "Test SQLite database initialized successfully."
                )
        except Exception as e:
            typer.echo(f"Error initializing test SQLite database: {e}")


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
    "ScanResultCRUD",
    # Vault Record
    "VaultRecord",
    "VaultRecordSchema",
    "VaultRecordCRUD",
    # Repo Record
    "RepoRecord",
    "RepoRecordSchema",
    "RepoRecordCRUD",
    # Document Index
    "DocumentIndexRecord",
    "DocumentIndexSchema",
    "DocumentIndexCRUD",
    # Input Record
    "InputRecord",
    "InputRecordSchema",
    "InputOut",
    "InputRecordCRUD",
    # Chunk Record
    "ChunkRecord",
    "ChunkRecordSchema",
    "ChunkRecordCRUD",
    # File Record
    "FileRecord",
    "FileRecordSchema",
    "FileLineSchema",
    "FileRecordCRUD",
    # Document Record
    "DocumentRecord",
    "DocumentRecordSchema",
    "ChunkModel",
    "ChunkList",
    "DocumentOut",
    "StringContentOut",
    "DocumentRecordCRUD",
    # File Line
    "FileLineRecord",
    "FileLineSchema",
    "FileLineCRUD",
]
