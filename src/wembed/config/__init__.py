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
_root_dir = Path(__file__).resolve().parent.parent.parent
_app_data_dir = _root_dir.parent / "data"

# Get storage path from environment or use default
_storage = os.getenv("APP_STORAGE", _app_data_dir)
_app_data_dir = Path(_storage).resolve() if _storage else Path(_app_data_dir).resolve()

# .env file path resolution
_app_dotenv = _root_dir.parent / ".env"

# Load environment variables from .env file
load_dotenv(_app_dotenv)

# set ollama host if provided
os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Setup paths
local_db_path = _app_data_dir / "local.db"
_md_vault = _app_data_dir / "md_vault"
_ignore_parts_path = _app_data_dir / "ignore_parts.json"
_ignore_ext_path = _app_data_dir / "ignore_ext.json"
_md_xref_path = _app_data_dir / "md_xref.json"
_headers_path = _app_data_dir / "headers.json"


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
HEADERS_CONFIG: Path = _headers_path
MAX_TOKENS: int = os.environ.get("MAX_TOKENS", 2048)
EMBEDDING_LENGTH: int = os.environ.get("EMBEDDING_LENGTH", 768)
EMBED_MODEL_HF_ID: str = os.environ.get("EMBED_MODEL_HF_ID", None)
EMBED_MODEL_NAME: str = os.environ.get("EMBED_MODEL_NAME", "nomic-embed-text")
LOCAL_DB_URI: str = os.environ.get("LOCAL_DB_URI", f"sqlite:///{local_db_path}")
HOST: str = os.environ.get("HOST", None) or os.getenv("COMPUTERNAME", None) or "unknown"
USER: str = os.environ.get("USER", None) or os.getenv("USERNAME", None) or "unknown"
SQLALCHEMY_DATABASE_URI: str = os.environ.get("SQLALCHEMY_DATABASE_URI", None)
MAX_FILE_SIZE: int = os.environ.get("MAX_FILE_SIZE", 3 * 1024 * 1024)  # 3 MB

VAULT_FOLDER = ".obsidian"
VAULT_EXTENSIONS = {".md"}


class Config(BaseSettings):
    """Application configuration using Pydantic BaseSettings."""

    db_path: str = local_db_path.as_posix()
    app_db_uri: str | None = SQLALCHEMY_DATABASE_URI
    local_db_uri: str = LOCAL_DB_URI
    md_vault: Path = MD_VAULT
    app_storage: Path = STORAGE
    ignore_parts: list[str] = IGNORE_PARTS
    ignore_extensions: list[str] = IGNORE_EXTENSIONS
    md_xref: dict[str, str] = MD_XREF
    headers: dict[str, str] = HEADERS
    embed_model_id: str = EMBED_MODEL_HF_ID
    embed_model_name: str = EMBED_MODEL_NAME
    embedding_length: int = int(EMBEDDING_LENGTH)
    max_tokens: int = int(MAX_TOKENS)
    host: str = HOST
    user: str = USER
    vault_folder: str = VAULT_FOLDER
    vault_extensions: set[str] = VAULT_EXTENSIONS
    max_file_size: int = int(MAX_FILE_SIZE)

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
    def app_db(self) -> Engine | None:
        """Get PostgreSQL database engine if URI is provided."""
        if self.app_db_uri:
            return create_engine(self.app_db_uri)
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


__all__ = [
    "Config",
    "app_config",
    "config_cli",
    "ppconfig_conf",
    "export_config",
    "_init_config",
    "STORAGE",
    "MD_VAULT",
    "LOCAL_DB_URI",
    "SQLALCHEMY_DATABASE_URI",
    "MAX_TOKENS",
    "EMBEDDING_LENGTH",
    "LOCAL_DB_URI",
    "HEADERS",
    "IGNORE_PARTS",
    "IGNORE_EXTENSIONS",
    "MD_XREF",
    "IS_INITIALIZED",
]


if __name__ == "__main__":
    config_cli()
