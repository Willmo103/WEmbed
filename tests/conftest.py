"""
Pytest configuration and shared fixtures for testing.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlite_utils import Database

# Import from your actual package structure
try:
    from . import Config
except ImportError:
    # If the package isn't installed, add parent directory to path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from . import Config


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config(temp_dir):
    """Create a temporary configuration for testing."""
    db_path = temp_dir / "test.db"
    vault_path = temp_dir / "vault"
    vault_path.mkdir(exist_ok=True)

    config = Config(
        db_path=db_path.as_posix(),
        app_storage=temp_dir,
        md_vault=vault_path,
        remote_db_uri=None,  # Use None for testing to avoid real DB connections
    )

    # Yield the config
    yield config

    # Cleanup: explicitly close database connections
    try:
        if hasattr(config, "local_db"):
            db = config.local_db
            if hasattr(db, "db") and hasattr(db.db, "close"):
                db.db.close()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def mock_database():
    """Mock database for testing without actual database operations."""
    mock_db = Mock(spec=Database)
    mock_db.table_names.return_value = ["test_table"]
    return mock_db


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "COMPUTERNAME": "test-machine",
            "USERNAME": "test-user",
            "INGESTOR_STORAGE": "",
            "SQLALCHEMY_DATABASE_URI": "",
        },
    ):
        yield


@pytest.fixture(scope="session")
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "max_tokens": 2048,
        "embedding_length": 768,
        "embed_model_id": "nomic-ai/nomic-embed-text-v1.5",
        "embed_model_name": "nomic-embed-text",
        "host": "test-host",
        "user": "test-user",
        "vault_folder": ".obsidian",
        "vault_extensions": {".md"},
    }


@pytest.fixture
def isolated_config(temp_dir, monkeypatch):
    """Create an isolated configuration that doesn't affect the global state."""
    # Mock the module-level variables to use temp directory
    monkeypatch.setattr("wembed.APP_STORAGE", temp_dir)
    monkeypatch.setattr("wembed.MD_VAULT", temp_dir / "vault")
    monkeypatch.setattr("wembed.local_db_path", temp_dir / "test.db")

    # Create a fresh config with isolated paths
    config = Config(
        app_storage=temp_dir,
        md_vault=temp_dir / "vault",
        db_path=(temp_dir / "test.db").as_posix(),
    )
    return config


@pytest.fixture(autouse=True)
def reset_initialization_flag(monkeypatch):
    """Reset the IS_INITIALIZED flag before each test."""
    monkeypatch.setattr("wembed.IS_INITIALIZED", False)


# Mark different types of tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Fixtures for specific components
@pytest.fixture
def mock_headers():
    """Mock headers configuration."""
    return {
        "User-Agent": "test-agent",
        "Accept": "application/json",
    }


@pytest.fixture
def mock_ignore_parts():
    """Mock ignore parts configuration."""
    return [
        "__pycache__",
        ".git",
        "node_modules",
    ]


@pytest.fixture
def mock_ignore_extensions():
    """Mock ignore extensions configuration."""
    return [".pyc", ".log", ".tmp"]


@pytest.fixture
def mock_md_xref():
    """Mock markdown cross-reference configuration."""
    return {
        "[[link]]": "reference",
        "![[embed]]": "embedded_content",
    }


# Performance testing fixture
@pytest.fixture
def performance_config():
    """Configuration optimized for performance testing."""
    return Config(
        max_tokens=1024,  # Smaller for faster tests
        embedding_length=256,  # Smaller for faster tests
    )


# Error condition fixtures
@pytest.fixture
def invalid_config_data():
    """Invalid configuration data for error testing."""
    return {
        "max_tokens": "not_an_int",  # Should be int
        "embedding_length": -1,  # Should be positive
        "vault_extensions": "not_a_set",  # Should be set
    }


@pytest.fixture
def cleanup_test_files():
    """Cleanup any test files created during testing."""
    test_files = []

    def register_file(filepath):
        test_files.append(Path(filepath))

    yield register_file

    # Cleanup after test
    for file_path in test_files:
        if file_path.exists():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil

                shutil.rmtree(file_path)


# Async fixtures for future async testing
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
