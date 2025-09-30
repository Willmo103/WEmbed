import os
import socket
from pathlib import Path
from typing import Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import CONFIG_DIR


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

    # --- Pydantic Settings Configuration ---
    model_config = SettingsConfigDict(
        json_file_encoding="utf-8",
        # Allow extra fields in the JSON file to be ignored
        extra="ignore",
    )

    def ensure_paths(self) -> None:
        """Ensure that all necessary directories exist."""
        self.md_vault_path.mkdir(parents=True, exist_ok=True)
