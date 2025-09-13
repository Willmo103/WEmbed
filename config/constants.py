import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlite_utils import Database


IS_INITIALIZED = False

# determine where to look for files:

# Root of the app
_root_dir = Path(__file__).resolve().parent.parent
_app_data_dir = _root_dir.parent / "data"

# or the storage path from the system
_storage = os.getenv("_STORAGE", _app_data_dir)

# Pick the storage path
_app_data_dir = Path(_storage).resolve() if _storage else Path(_app_data_dir).resolve()

# .env file path resolution
_app_dotenv = _root_dir.parent / ".env"

# Load environment variables from .env file
load_dotenv(_app_dotenv)

# CRITICAL we have a connection to POSTGRES
_postgres_uri = os.getenv("PG_DB_URL", None)
if not _postgres_uri:
    print("WARNING: PG_DB_URL not set in environment, Postgres DB will be disabled")

_host = os.getenv("COMPUTERNAME", "unknown")
_user = os.getenv("USERNAME", "unknown")

# setup db paths
_md_db = _app_data_dir / "md.db"
_repo_db = _app_data_dir / "repo.db"

# setup vault dir
_md_vault = _app_data_dir / "md_vault"

# setup config files
_ignore_parts_path = _app_data_dir / "ignore_parts.json"
_ignore_ext_path = _app_data_dir / "ignore_ext.json"
_md_xref = _app_data_dir / "md_xref.json"


def _init_config():
    global IS_INITIALIZED
    if IS_INITIALIZED:
        return
    Path(_app_data_dir).mkdir(parents=True, exist_ok=True)
    Path(_app_dotenv).touch(exist_ok=True)
    Path(_repo_db).touch(exist_ok=True)
    Path(_md_db).touch(exist_ok=True)
    IS_INITIALIZED = True


if not IS_INITIALIZED:
    _init_config()


# sqlite-utils Databases
MD_DB: Database = Database(_md_db)
REPO_DATABASE: Database = Database(_repo_db)

# data dirs
STORAGE: Path = _app_data_dir
MD_VAULT: Path = _md_vault
IGNORE_PARTS_CONFIG: Path = _ignore_parts_path
IGNORE_EXTENSIONS_CONFIG: Path = _ignore_ext_path
MD_XREF_CONFIG: Path = _md_xref


MAX_TOKENS: int = 2048
EMBEDDING_LENGTH: int = 768
EMBED_MODEL_ID: str = "nomic-ai/nomic-embed-text-v1.5"
EMBED_MODEL_NAME: str = "nomic-embed-text"

OBSIDIAN_EXE: str = (
    f"C:\\Users\\{_user}\\AppData\\Local\\Programs\\Obsidian\\Obsidian.exe"
)

SQLITE_REPO_URI: str = f"sqlite:///{_repo_db}"
SQLITE_MD_URI: str = f"sqlite:///{_md_db}"
HOST: str = _host
USER: str = _user
POSTGRES_URI: str = _postgres_uri


def print_config():
    print(
        f"""
_root_dir: {_root_dir}
_app_data_dir: {_app_data_dir}
_host: {_host}
_user: {_user}
_md_vault: {_md_vault}
_md_xref: {_md_xref}
_ignore_parts_path: {_ignore_parts_path}
_ignore_ext_path: {_ignore_ext_path}
_repo_uri: {SQLITE_REPO_URI.replace('\\', '/')}
_md_uri: {SQLITE_MD_URI.replace('\\', '/')}
"""
    )


print_config()
