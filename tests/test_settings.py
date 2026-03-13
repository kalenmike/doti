"""Tests for doti.core.settings module."""

import tempfile
import pytest
from pathlib import Path
import yaml
from doti.core.settings import SettingsManager, _load_yaml


class TestLoadYaml:
    """Tests for the _load_yaml helper function."""

    def test_load_yaml_with_valid_file(self):
        """Test loading a valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"key": "value", "number": 42}, f)
            f.flush()
            path = Path(f.name)

        result = _load_yaml(path)
        assert result == {"key": "value", "number": 42}

        path.unlink()

    def test_load_yaml_with_none(self):
        """Test loading None returns empty dict."""
        result = _load_yaml(None)
        assert result == {}

    def test_load_yaml_with_empty_file(self):
        """Test loading empty YAML file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            path = Path(f.name)

        result = _load_yaml(path)
        assert result == {}

        path.unlink()


class TestSettingsManager:
    """Tests for the SettingsManager class."""

    def test_settings_manager_with_source(self):
        """Test SettingsManager initialization with source path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            settings = SettingsManager(config=None, source=str(source))

            assert settings.source == source.resolve()

    def test_settings_manager_source_defaults_to_home(self):
        """Test source defaults to user's home when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            settings = SettingsManager(config=None, source=str(source))

            assert settings.target == Path("~").expanduser().resolve()

    def test_settings_manager_with_config_file(self):
        """Test loading settings from config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            config_path = source / ".config" / "doti" / "settings.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                "dotfiles": str(source),
                "confirm_changes": False,
                "backup_suffix": ".backup",
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            settings = SettingsManager(config=str(config_path))

            assert settings.confirm_changes is False
            assert settings.backup_suffix == ".backup"

    def test_settings_manager_default_values(self):
        """Test default values when not specified in config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))

            assert settings.link_icon == "↗"
            assert settings.backup_icon == "⊚"
            assert settings.backup_suffix == ".bkp"
            assert settings.add_dot is True
            assert settings.confirm_changes is True

    def test_settings_manager_custom_values(self):
        """Test custom values from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            config_path = source / "config.yaml"

            config_data = {
                "dotfiles": str(source),
                "link_icon": "[L]",
                "backup_icon": "[B]",
                "backup_suffix": ".bak",
                "add_dot": False,
                "confirm_changes": False,
            }
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            settings = SettingsManager(config=str(config_path))

            assert settings.link_icon == "[L]"
            assert settings.backup_icon == "[B]"
            assert settings.backup_suffix == ".bak"
            assert settings.add_dot is False
            assert settings.confirm_changes is False

    def test_find_config_path_explicit(self):
        """Test explicit config path is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            config_path = source / "my_config.yaml"
            config_path.write_text("dotfiles: .\n")

            settings = SettingsManager(config=str(config_path), source=str(source))

            assert settings.config_path == config_path.resolve()

    def test_find_config_path_in_source(self):
        """Test config path is searched in source directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            config_location = source / ".config" / "doti" / "settings.yaml"
            config_location.parent.mkdir(parents=True, exist_ok=True)
            config_location.write_text("dotfiles: .\n")

            settings = SettingsManager(config=None, source=str(source))

            assert settings.config_path == config_location.resolve()

    def test_find_config_path_no_config_returns_none(self):
        """Test returns None when no config found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))

            assert settings.config_path == config.resolve()
