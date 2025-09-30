"""
Logging configuration for the application.
"""

from logging import getLogger
from logging.config import dictConfig
from pathlib import Path


def setup_logging(logs_dir: Path):
    """Set up logging configuration."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "app.log"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "INFO",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "filename": str(log_file),
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }

    dictConfig(logging_config)
    return getLogger("wembed")
