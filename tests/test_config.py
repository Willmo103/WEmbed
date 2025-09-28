# tests/test_config.py

import json
import os
import shutil
from pathlib import Path

import pytest

# Test subject module
from wembed import config


@pytest.fixture
def temp_config_dirs(tmp_path):
    """Create temporary prod and dev config directories for testing."""
    # tmp_path is a pytest fixture providing a temporary directory

    # Fake dev dir: <tmp_path>/project/data
    dev_dir = tmp_path / "project" / "data"
    dev_dir.mkdir(parents=True)

    # Fake prod dir: <tmp_path>/.wembed
    prod_dir = tmp_path / ".wembed"
    prod_dir.mkdir(parents=True)

    # Yield the paths and the project root
    yield {"dev": dev_dir, "prod": prod_dir, "root": tmp_path / "project"}

    # Cleanup is handled automatically by pytest's tmp_path fixture


def test_prod_mode_loads_from_home_dir(monkeypatch, temp_config_dirs):
    """Verify that without DEV flags, config loads from the 'home' directory."""
    # Arrange: Point the config module's constants to our temp dirs
    monkeypatch.setattr(config, "PROD_CONFIG_DIR", temp_config_dirs["prod"])
    monkeypatch.setattr(config, "DEV_CONFIG_DIR", temp_config_dirs["dev"])

    # Ensure no dev flags are set
    monkeypatch.delenv("DEV", raising=False)
    monkeypatch.delenv("TESTING", raising=False)

    # Create a dummy config file in the PROD location
    prod_appconfig_path = temp_config_dirs["prod"] / "appconfig.json"
    with open(prod_appconfig_path, "w") as f:
        json.dump({"max_tokens": 9999}, f)

    # Act: Reload the config logic and instantiate the class
    config.CONFIG_DIR = config.get_config_dir()
    settings = config.AppConfig()

    # Assert: Check that the value from the PROD file was loaded
    assert settings.max_tokens == 9999
    assert config.CONFIG_DIR == temp_config_dirs["prod"]


@pytest.mark.parametrize("dev_flag", ["DEV", "TESTING"])
def test_dev_mode_loads_from_project_data(monkeypatch, temp_config_dirs, dev_flag):
    """Verify that with a DEV flag, config loads from the project 'data' directory."""
    # Arrange: Point the config module's constants to our temp dirs
    monkeypatch.setattr(config, "PROD_CONFIG_DIR", temp_config_dirs["prod"])
    monkeypatch.setattr(config, "DEV_CONFIG_DIR", temp_config_dirs["dev"])

    # Set the appropriate dev/testing flag
    monkeypatch.setenv(dev_flag, "1")

    # Create dummy config files in BOTH locations to ensure it picks the right one
    prod_appconfig_path = temp_config_dirs["prod"] / "appconfig.json"
    with open(prod_appconfig_path, "w") as f:
        json.dump({"max_tokens": 9999}, f)

    dev_appconfig_path = temp_config_dirs["dev"] / "appconfig.json"
    with open(dev_appconfig_path, "w") as f:
        json.dump({"max_tokens": 1234}, f)

    # Act: Reload the config logic and instantiate the class
    config.CONFIG_DIR = config.get_config_dir()
    settings = config.AppConfig()

    # Assert: Check that the value from the DEV file was loaded
    assert settings.max_tokens == 1234
    assert config.CONFIG_DIR == temp_config_dirs["dev"]


def test_dev_mode_raises_error_if_dir_missing(monkeypatch, temp_config_dirs):
    """Verify that dev mode fails if the 'data' directory doesn't exist."""
    # Arrange: Point to our temp dirs, but REMOVE the dev directory
    monkeypatch.setattr(config, "PROD_CONFIG_DIR", temp_config_dirs["prod"])
    monkeypatch.setattr(config, "DEV_CONFIG_DIR", temp_config_dirs["dev"])
    shutil.rmtree(temp_config_dirs["dev"])  # Remove the directory

    monkeypatch.setenv("DEV", "1")

    # Act & Assert: Check that the specified error is raised
    with pytest.raises(FileNotFoundError, match="Development mode is active"):
        config.get_config_dir()
