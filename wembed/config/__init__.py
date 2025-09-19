import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings
from sqlalchemy import Engine, create_engine
from sqlite_utils import Database

from .headers import HEADERS
from .ignore_ext import IGNORE_EXTENSIONS
from .ignore_parts import IGNORE_PARTS
from .md_xref import MD_XREF

IS_INITIALIZED = False

# Path determination logic from constants.py
_root_dir = Path(__file__).resolve().parent.parent
_app_data_dir = _root_dir.parent / "data"

# Get storage path from environment or use default
_storage = os.getenv("INGESTOR_STORAGE", _app_data_dir)
_app_data_dir = Path(_storage).resolve() if _storage else Path(_app_data_dir).resolve()

# .env file path resolution
_app_dotenv = _root_dir.parent / ".env"

# Load environment variables from .env file
load_dotenv(_app_dotenv)

# set ollama host if provided
os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Environment variables
_sqlalchemy_uri = os.getenv("SQLALCHEMY_DATABASE_URI", None)
_host = os.getenv("COMPUTERNAME", "unknown")
_user = os.getenv("USERNAME", "unknown")

# Setup paths
local_db_path = _app_data_dir / "local.db"
_md_vault = _app_data_dir / "md_vault"
_ignore_parts_path = _app_data_dir / "ignore_parts.json"
_ignore_ext_path = _app_data_dir / "ignore_ext.json"
_md_xref_path = _app_data_dir / "md_xref.json"
_headers_path = _app_data_dir / "headers.json"
_config_path = _app_data_dir / "config.json"


def _init_config():
    """Initialize configuration directories and files."""
    global IS_INITIALIZED
    if IS_INITIALIZED:
        return
    Path(_app_data_dir).mkdir(parents=True, exist_ok=True)
    Path(_app_dotenv).touch(exist_ok=True)
    Path(local_db_path).touch(exist_ok=True)
    Path(_headers_path).touch(exist_ok=True)
    IS_INITIALIZED = True


if not IS_INITIALIZED:
    _init_config()

# Constants
STORAGE: Path = _app_data_dir
MD_VAULT: Path = _md_vault
IGNORE_PARTS_CONFIG: Path = _ignore_parts_path
IGNORE_EXTENSIONS_CONFIG: Path = _ignore_ext_path
MD_XREF_CONFIG: Path = _md_xref_path

MAX_TOKENS: int = 2048
EMBEDDING_LENGTH: int = 768
EMBED_MODEL_HF_ID: str = "nomic-ai/nomic-embed-text-v1.5"
EMBED_MODEL_NAME: str = "nomic-embed-text"

OBSIDIAN_EXE: str = (
    f"C:\\Users\\{_user}\\AppData\\Local\\Programs\\Obsidian\\Obsidian.exe"
)

LOCAL_DB_URI: str = f"sqlite:///{local_db_path}"
HOST: str = _host
USER: str = _user
POSTGRES_URI: str = _sqlalchemy_uri
VAULT_FOLDER = ".obsidian"
VAULT_EXTENSIONS = {".md"}


class Config(BaseSettings):
    """Application configuration using Pydantic BaseSettings."""

    db_path: str = local_db_path.as_posix()
    remote_db_uri: str | None = POSTGRES_URI
    local_db_uri: str = LOCAL_DB_URI
    md_vault: Path = MD_VAULT
    app_storage: Path = STORAGE
    ignore_parts: list[str] = IGNORE_PARTS
    ignore_extensions: list[str] = IGNORE_EXTENSIONS
    md_xref: dict[str, str] = MD_XREF
    headers: dict[str, str] = HEADERS
    embed_model_id: str = EMBED_MODEL_HF_ID
    embed_model_name: str = EMBED_MODEL_NAME
    embedding_length: int = EMBEDDING_LENGTH
    max_tokens: int = MAX_TOKENS
    host: str = HOST
    user: str = USER
    vault_folder: str = VAULT_FOLDER
    vault_extensions: set[str] = VAULT_EXTENSIONS

    model_config = {
        "json_encoders": {
            Path: lambda v: v.as_posix(),
            Database: lambda v: str(v),
            Engine: lambda v: str(v),
        }
    }

    @computed_field
    def local_db(self) -> Database:
        """Get local SQLite database connection."""
        return Database(self.db_path)

    @computed_field
    def postgres_db(self) -> Engine | None:
        """Get PostgreSQL database engine if URI is provided."""
        if self.remote_db_uri:
            return create_engine(self.remote_db_uri)
        return None


# Global configuration instance
app_config = Config()

# CLI setup
config_cli = typer.Typer(
    name="config", no_args_is_help=True, help="Configuration commands"
)


def ppconfig_conf():
    """Pretty print configuration as JSON."""
    print(app_config.model_dump_json(indent=4))


def export_config(fp: str):
    """Export configuration to a JSON file."""
    fp = Path(fp).resolve() / "file_injester.config.json"
    with open(fp, "w") as f:
        f.write(
            app_config.model_dump_json(
                indent=4, exclude={"md_db", "repo_db", "postgres_db"}
            )
        )


@config_cli.command(name="show")
def show_config():
    """Show current configuration."""
    ppconfig_conf()


@config_cli.command(name="export")
def export_config_command(
    fp: str = typer.Argument(
        ...,
        file_okay=False,
        dir_okay=True,
        exists=False,
        help="Directory to export config file to",
    )
):
    """Export configuration to specified directory."""
    export_config(fp)


if __name__ == "__main__":
    config_cli()
