import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlite_utils import Database


IS_INITIALIZED = False

_root_dir = Path(__file__).resolve().parent.parent
_app_data_dir = os.getenv("APP_DATA_DIR", _root_dir.parent / "data")
_storage = os.getenv("STORAGE", _app_data_dir)
_app_data_dir = Path(_storage).resolve() if _storage else Path(_app_data_dir).resolve()

_host = os.getenv("COMPUTERNAME", "unknown")
_user = os.getenv("USERNAME", "unknown")

# setup db paths
_md_db = _app_data_dir / "md.db"
_repo_db = _app_data_dir / "repo.db"

# setup vault dir
_md_vault = _app_data_dir / "md_vault"

# setup config files
_app_dotenv = _root_dir.parent / ".env"
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


load_dotenv(_app_dotenv)

# sqlite-utils Databases
MD_DB = Database(_md_db)
REPO_DATABASE = Database(_repo_db)

# data dirs
STORAGE = _app_data_dir
MD_VAULT = _md_vault
IGNORE_PARTS_CONFIG = _ignore_parts_path
IGNORE_EXTENSIONS_CONFIG = _ignore_ext_path
MD_XREF_CONFIG = _md_xref


MAX_TOKENS = 2048
EMBEDDING_LENGTH = 768
EMBED_MODEL_ID = "nomic-ai/nomic-embed-text-v1.5"
EMBED_MODEL_NAME = "nomic-embed-text"

OBSIDIAN_EXE = f"C:\\Users\\{_user}\\AppData\\Local\\Programs\\Obsidian\\Obsidian.exe"


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
"""
    )


print_config()
