import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlite_utils import Database

from ignore_ext import IGNORE_EXTENSIONS
from ignore_parts import IGNORE_PARTS
from md_xref import MD_XREF

_this_dir = Path(__file__).resolve().parent
_app_data_dir = os.getenv("APP_DATA_DIR", _this_dir.parent / "data")
_app_data_dir = Path(_app_data_dir).resolve()

_host = os.getenv("COMPUTERNAME", "unknown")
_user = os.getenv("USERNAME", "unknown")

# private constants for setup
_app_dotenv = _this_dir.parent / ".env"

_default_repos_db = os.getenv("REPO_DB", _app_data_dir / "repos.db")
_md_db = os.getenv("MD_DB", _app_data_dir / "md.db")
_md_vault = os.getenv("MD_VAULT", _app_data_dir / "md_vault")
_ignore_parts_path = os.getenv("IGNORE_PARTS_PATH", _app_data_dir / "ignore_parts.json")
_ignore_ext_path = os.getenv("IGNORE_EXT_PATH", _app_data_dir / "ignore_ext.json")
_md_xref = os.getenv("MD_XREF", _app_data_dir / "md_xref.json")
_md_xref = Path(_md_xref).resolve()

load_dotenv(_app_dotenv)

MD_DB = Database(_md_db)
REPO_DATABASE = Database(_default_repos_db)
MD_VAULT = Path(_md_vault).resolve()
REPO_DATABASE = Path(_default_repos_db).resolve()
IGNORE_PARTS_CONFIG = Path(_ignore_parts_path).resolve()
IGNORE_EXTENSIONS_CONFIG = Path(_ignore_ext_path).resolve()
MD_XREF_CONFIG = Path(_md_xref).resolve()


OBSIDIAN_EXE = f"C:\\Users\\{_user}\\AppData\\Local\\Programs\\Obsidian\\Obsidian.exe"


def _load_md_xref() -> None:
    IGNORE_EXTENSIONS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not MD_XREF_CONFIG.exists():
        with open(MD_XREF_CONFIG, "w", encoding="utf-8") as f:
            json.dump(sorted(MD_XREF), f, indent=2)
    else:
        with open(MD_XREF_CONFIG, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    MD_XREF.update(data)
            except json.JSONDecodeError:
                # if file corrupt/empty, rewrite defaults
                with open(MD_XREF_CONFIG, "w", encoding="utf-8") as out:
                    json.dump(sorted(MD_XREF), out, indent=2)


def _load_ignore_parts() -> None:
    IGNORE_PARTS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not IGNORE_PARTS_CONFIG.exists():
        with open(IGNORE_PARTS_CONFIG, "w", encoding="utf-8") as f:
            json.dump(sorted(IGNORE_PARTS), f, indent=2)
    else:
        with open(IGNORE_PARTS_CONFIG, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    IGNORE_PARTS.update(data)
            except json.JSONDecodeError:
                # if file corrupt/empty, rewrite defaults
                with open(IGNORE_PARTS_CONFIG, "w", encoding="utf-8") as out:
                    json.dump(sorted(IGNORE_PARTS), out, indent=2)


def _load_ignore_extensions() -> None:
    IGNORE_EXTENSIONS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    if not IGNORE_EXTENSIONS_CONFIG.exists():
        with open(IGNORE_EXTENSIONS_CONFIG, "w", encoding="utf-8") as f:
            json.dump(sorted(IGNORE_EXTENSIONS), f, indent=2)
    else:
        with open(IGNORE_EXTENSIONS_CONFIG, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    IGNORE_EXTENSIONS.update(data)
            except json.JSONDecodeError:
                with open(IGNORE_EXTENSIONS_CONFIG, "w", encoding="utf-8") as out:
                    json.dump(sorted(IGNORE_EXTENSIONS), out, indent=2)


def init_config():
    _app_data_dir.mkdir(parents=True, exist_ok=True)
    _app_dotenv.touch(exist_ok=True)
    _default_repos_db.touch(exist_ok=True)
    _md_db.touch(exist_ok=True)
