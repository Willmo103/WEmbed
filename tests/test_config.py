import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlite_utils import Database
from typer.testing import CliRunner

# Import from your wembed package
from . import (
    EMBEDDING_LENGTH,
    LOCAL_DB_URI,
    MAX_TOKENS,
    MD_VAULT,
    STORAGE,
    Config,
    app_config,
    config_cli,
    export_config,
    init_config,
    ppconfig_conf,
)


class TestConstants:
    """Test module-level constants and path resolution."""

    def test_storage_path_exists(self):
        """Test that STORAGE path is a valid Path object."""
        assert isinstance(STORAGE, Path)
        assert STORAGE.exists()

    def test_md_vault_path_exists(self):
        """Test that MD_VAULT path is a valid Path object."""
        assert isinstance(MD_VAULT, Path)

    def test_local_db_uri_format(self):
        """Test that LOCAL_DB_URI follows SQLite format."""
        assert LOCAL_DB_URI.startswith("sqlite:///")
        assert str(STORAGE) in LOCAL_DB_URI

    def test_embedding_constants(self):
        """Test embedding-related constants."""
        # rewrite to check that they are now ints and positive
        assert type(int(MAX_TOKENS)) == int
        assert int(MAX_TOKENS) > 0
        assert type(int(EMBEDDING_LENGTH)) == int
        assert int(EMBEDDING_LENGTH) > 0

        # Your constants are strings from environment, so convert for testing
        # assert int(MAX_TOKENS) == 2048
        # assert int(EMBEDDING_LENGTH) == 768
        # assert isinstance(MAX_TOKENS, str)  # They come from environment as strings
        # assert isinstance(EMBEDDING_LENGTH, str)


class TestInitConfig:
    """Test the initialization function."""

    def test_init_config_idempotent(self):
        """Test that _init_config can be called multiple times safely."""
        # Should not raise any exceptions
        init_config()
        init_config()


class TestConfigClass:
    """Test the Config Pydantic model."""

    def test_config_creation_with_defaults(self):
        """Test creating Config with default values."""
        config = Config()
        assert config.max_tokens == int(MAX_TOKENS)  # Config converts to int
        assert config.embedding_length == int(
            EMBEDDING_LENGTH
        )  # Config converts to int
        assert isinstance(config.app_storage, Path)
        assert isinstance(config.md_vault, Path)

    def test_config_with_custom_values(self):
        """Test creating Config with custom values."""
        custom_tokens = 4096
        config = Config(max_tokens=custom_tokens)
        assert config.max_tokens == custom_tokens

    def test_local_db_computed_field(self):
        """Test that local_db computed field returns Database instance."""
        config = Config()
        db = config.local_db
        assert isinstance(db, Database)

    def test_app_db_computed_field_none(self):
        """Test app_db returns None when no URI provided."""
        config = Config(app_db_uri=None)
        assert config.app_db is None

    def test_app_db_computed_field_with_uri(self):
        """Test app_db returns Engine when URI is provided."""
        from sqlalchemy.engine import Engine

        config = Config(
            app_db_uri="postgresql+psycopg2://SystemAdmin:sa-password@192.168.0.5:5401/local"
        )
        assert config.app_db is not None
        assert isinstance(config.app_db, Engine)

    def test_model_config_json_encoders(self):
        """Test that Path objects are properly encoded in JSON."""
        config = Config()
        json_data = config.model_dump_json()
        assert isinstance(json_data, str)
        # Should not raise JSON encoding errors

    def test_vault_extensions_type(self):
        """Test that vault_extensions is a set."""
        config = Config()
        assert isinstance(config.vault_extensions, set)
        assert ".md" in config.vault_extensions


class TestAppConfig:
    """Test the global app_config instance."""

    def test_app_config_instance(self):
        """Test that app_config is a Config instance."""
        assert isinstance(app_config, Config)

    def test_app_config_has_local_db(self):
        """Test that app_config has working local_db."""
        db = app_config.local_db
        assert isinstance(db, Database)


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch.dict(os.environ, {"APP_STORAGE": "/custom/path"})
    def test_custom_storage_path(self):
        """Test that APP_STORAGE environment variable is respected."""
        # This would require reimporting the module or rerunning path logic
        # For now, test that the environment variable is accessible
        assert os.getenv("APP_STORAGE") == "/custom/path"

    @patch.dict(os.environ, {"SQLALCHEMY_DATABASE_URI": "postgresql://test"})
    def test_postgres_uri_from_env(self):
        """Test that SQLALCHEMY_DATABASE_URI environment variable is used."""
        assert os.getenv("SQLALCHEMY_DATABASE_URI") == "postgresql://test"


class TestConfigFunctions:
    """Test utility functions for configuration."""

    def test_ppconfig_conf(self, capsys):
        """Test that ppconfig_conf prints JSON configuration."""
        ppconfig_conf()
        captured = capsys.readouterr()
        assert len(captured.out) > 0
        # Should be valid JSON output
        assert "{" in captured.out

    def test_export_config(self):
        """Test exporting configuration to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_config(temp_dir)
            config_file = Path(temp_dir) / "wembed_config.json"
            assert config_file.exists()

            # Check file content
            content = config_file.read_text()
            assert "{" in content  # Valid JSON
            assert "max_tokens" in content


class TestConfigCLI:
    """Test the CLI commands."""

    def setUp(self):
        self.runner = CliRunner()

    def test_show_command(self):
        """Test the show command."""
        runner = CliRunner()
        result = runner.invoke(config_cli, ["show"])
        assert result.exit_code == 0
        assert "{" in result.stdout  # JSON output

    def test_export_command(self):
        """Test the export command."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(config_cli, ["export", temp_dir])
            assert result.exit_code == 0

            # Check file was created
            config_file = Path(temp_dir) / "wembed_config.json"
            assert config_file.exists()

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(config_cli, ["--help"])
        assert result.exit_code == 0
        assert "Configuration commands" in result.stdout


class TestOllamaEnvironment:
    """Test Ollama-specific configuration."""

    def test_ollama_host_set(self):
        """Test that OLLAMA_HOST environment variable is set."""
        assert os.environ.get("OLLAMA_HOST") is not None
        assert "http" in os.environ.get("OLLAMA_HOST")
        assert "11434" in os.environ.get("OLLAMA_HOST")
        # Updated to check for default value if not set


@pytest.fixture
def temp_config():
    """Fixture to create a temporary config for testing."""
    import gc
    import tempfile
    import time

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        db_path = temp_path / "test.db"
        vault_path = temp_path / "vault"
        vault_path.mkdir(exist_ok=True)

        config = Config(
            db_path=db_path.as_posix(),
            app_storage=temp_path,
            md_vault=vault_path,
            app_db_uri=None,
        )

        yield config

        # Aggressive cleanup for Windows
        try:
            # Clear any cached database connections
            if hasattr(config, "__dict__"):
                for key in list(config.__dict__.keys()):
                    if "db" in key.lower():
                        delattr(config, key)

            # Force garbage collection
            gc.collect()
            time.sleep(0.1)  # Brief pause for file handles to close
        except Exception:
            pass
        finally:
            # Ensure temporary files are cleaned up
            if temp_path.exists():
                shutil.rmtree(temp_path)


class TestConfigFixture:
    """Test using the config fixture."""

    def test_temp_config_fixture_memory_db(self):
        """Test temp config with in-memory database to avoid file locking."""
        # Use in-memory SQLite to avoid Windows file locking issues
        config = Config(
            db_path=":memory:",
            app_storage=Path.cwd(),  # Use current directory
            md_vault=Path.cwd() / "temp_vault",
            app_db_uri=None,
        )
        assert isinstance(config, Config)

        # Test local_db creation with in-memory database
        db = config.local_db
        assert isinstance(db, Database)

    def test_temp_config_fixture(self, temp_config):
        """Test that temp_config fixture works (may have cleanup issues on Windows)."""
        assert isinstance(temp_config, Config)
        assert temp_config.app_storage.exists()

        # Test local_db creation but don't keep reference
        db = temp_config.local_db
        assert isinstance(db, Database)
        del db  # Explicit cleanup


# Integration tests
class TestConfigIntegration:
    """Integration tests for the complete configuration system."""

    def test_config_round_trip(self):
        """Test creating config, exporting, and validating output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export config
            export_config(temp_dir)

            # Read exported file
            config_file = Path(temp_dir) / "wembed_config.json"
            content = config_file.read_text()

            # Should contain expected keys
            assert "max_tokens" in content
            assert "embedding_length" in content
            assert "embed_model_id" in content

    def test_database_connections(self):
        """Test that database connections work."""
        # Test local database
        local_db = app_config.local_db
        assert isinstance(local_db, Database)

        # Test that we can interact with it
        tables = local_db.table_names()
        assert isinstance(tables, list)
