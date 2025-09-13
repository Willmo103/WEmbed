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

# Host and User
_host = os.getenv("COMPUTERNAME", "unknown")
_user = os.getenv("USERNAME", "unknown")

# setup db paths
local_db_path = _app_data_dir / "md.db"

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
    Path(local_db_path).touch(exist_ok=True)
    IS_INITIALIZED = True


if not IS_INITIALIZED:
    _init_config()


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

LOCAL_DB_URI: str = f"sqlite:///{local_db_path}"
HOST: str = _host
USER: str = _user
POSTGRES_URI: str = _postgres_uri
