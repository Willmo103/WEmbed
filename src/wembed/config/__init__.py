"""
Configuration management for WEmbed application.
This module handles loading settings from JSON files located in either a
production directory (~/.wembed) or a development directory (./data).
It uses Pydantic for structured settings management and validation.
It also provides helper functions to load additional configuration data
from satellite JSON files.
"""

import json
import os
import socket
from pathlib import Path
from typing import Any, Dict, List, Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define the two possible locations for configuration files
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROD_CONFIG_DIR = Path.home() / ".wembed"
DEV_CONFIG_DIR = PROJECT_ROOT / "data"


def is_dev_mode() -> bool:
    """Check environment variables to determine if in dev/testing mode."""
    dev_flag = os.environ.get("DEV", "false").lower() in ("true", "1", "t")
    testing_flag = os.environ.get("TESTING", "false").lower() in (
        "true",
        "1",
        "t",
    )
    return dev_flag or testing_flag


def get_config_dir() -> Path:
    """Return the appropriate configuration directory based on the environment."""
    if is_dev_mode():
        # In dev/test mode, config files MUST exist here.
        if not DEV_CONFIG_DIR.exists():
            raise FileNotFoundError(
                f"Development mode is active, but the required config directory "
                f"was not found: {DEV_CONFIG_DIR}"
            )
        return DEV_CONFIG_DIR
    else:
        # In production, we ensure the directory exists.
        PROD_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return PROD_CONFIG_DIR


# Determine the active configuration directory ONCE on import.
CONFIG_DIR = get_config_dir()


# region: Helper functions to load satellite JSON files
def _load_json_from_config_dir(filename: str, default: Any) -> Any:
    """Loads a specific JSON file from the config dir, with a default fallback."""
    file_path = CONFIG_DIR / filename
    if file_path.exists():
        with open(file_path, "r") as f:
            return json.load(f)
    return default


# --- Helpers to load specific satellite config files ---
def load_headers() -> Dict[str, str]:
    return (
        _load_json_from_config_dir("headers.json", default={})
        if _load_json_from_config_dir("headers.json", default={})
        else {}
    )


def load_ignore_extensions() -> List[str]:
    return (
        _load_json_from_config_dir("ignore_exts.json", default=[])
        if _load_json_from_config_dir("ignore_exts.json", default=[])
        else []
    )


def load_ignore_parts() -> List[str]:
    return (
        _load_json_from_config_dir("ignore_parts.json", default=[])
        if _load_json_from_config_dir("ignore_parts.json", default=[])
        else []
    )


def load_md_xref() -> Dict[str, Any]:
    return (
        _load_json_from_config_dir("md_xref.json", default={})
        if _load_json_from_config_dir("md_xref.json", default={})
        else {}
    )


# - endregion


# --- Main AppConfig class ---
class AppConfig(BaseSettings):
    """
    Loads application settings from `appconfig.json` located in the
    appropriate production or development directory.
    """

    # --- Database ---
    sqlalchemy_db_uri: str = Field(
        default="postgresql://admin:wembed-admin-pass@localhost:5454/wembed",
        description="The full SQLAlchemy URI for the PostgreSQL database.",
    )

    # --- Core Paths ---
    @property
    def md_vault_path(self) -> Path:
        """Path to the directory where markdown files are stored."""
        return CONFIG_DIR / "md_vault"

    # --- Embedding Model ---
    embed_model_id: str = "nomic-ai/nomic-embed-text-v1.5"
    embed_model_name: str = "nomic-embed-text"
    embedding_length: int = 768
    max_tokens: int = 2048

    # --- System and User Info ---
    host: str = Field(default_factory=socket.gethostname)
    user: str = Field(default_factory=lambda: os.getenv("USER", "unknown_user"))

    # --- File Processing ---
    max_file_size_bytes: int = 3 * 1024 * 1024  # 3MB
    vault_folder_name: str = ".obsidian"
    vault_extensions: Set[str] = {".md"}

    # --- Data loaded from satellite JSON files ---
    headers: Dict[str, str] = Field(default_factory=load_headers)
    ignore_extensions: List[str] = Field(default_factory=load_ignore_extensions)
    ignore_parts: List[str] = Field(default_factory=load_ignore_parts)
    md_xref: Dict[str, Any] = Field(default_factory=load_md_xref)

    # --- Pydantic Settings Configuration ---
    model_config = SettingsConfigDict(
        # The primary source for settings is this JSON file.
        # Environment variables will still override it.
        json_file=CONFIG_DIR / "appconfig.json",
        json_file_encoding="utf-8",
        # Allow extra fields in the JSON file to be ignored
        extra="ignore",
    )


# - endregion
