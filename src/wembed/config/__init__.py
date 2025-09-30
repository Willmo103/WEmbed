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
from pathlib import Path
from typing import Any

from ..constants import PROD_CONFIG_DIR, PROJECT_ROOT
from ._logging import setup_logging

# Define the two possible locations for configuration files
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


DEV_MODE = is_dev_mode()


def get_config_dir() -> Path:
    """Return the appropriate configuration directory based on the environment."""
    if DEV_MODE:
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
ROOT_LOGGER = setup_logging(CONFIG_DIR / "logs")
