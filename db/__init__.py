from tkinter.filedialog import test
import psycopg2
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import Session, sessionmaker
from ._base import Base
from config import app_config
import typer

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
        from . import models

        models.Base.metadata.create_all(_get_engine(uri))
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
        return sessionmaker(autocommit=False, autoflush=False, bind=_get_engine(uri))()
    except Exception:
        return None


def get_session() -> Session:
    return get_session_remote() or get_session_local()


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
    test_db: bool = typer.Option(
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
        success, msg = _init_db(_remote_uri, force)
    if local:
        success, msg = _init_db(_local_uri, force)
    if test:
        success, msg = _init_db("sqlite:///test_db.db", force=True)
    if not success:
        print(f"Database initialization failed: {msg}")
    else:
        print(msg or "Database initialized successfully.")
