"""Settings management for Doti configuration."""

from pathlib import Path
from functools import cached_property
import yaml
from importlib import resources
import sys
from typing import Any, Dict, Optional


def _load_yaml(path: Optional[Path], strict: bool = False) -> Dict[str, Any]:
    """
    Load a YAML file.

    Args:
        path: Path to the YAML file.
        strict: If True, raises FileNotFoundError if path is None or invalid.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If strict is True and the file does not exist.
        yaml.YAMLError: If the file exists but contains invalid YAML.
    """
    if not path or not path.is_file():
        if strict:
            raise FileNotFoundError(f"Required file not found at: {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class SettingsManager:
    """
    Manages configuration settings for Doti, loading from user config
    and default values.

    Attributes:
        config_path: Path to the user configuration file.
        default_path: Path to the default configuration.
        settings: Merged dictionary of default and user settings.
    """

    def __init__(
        self, config: Optional[str] = None, source: Optional[str] = None
    ) -> None:
        """
        Initialize the settings manager.

        Args:
            config: Optional path to a user configuration file.
            source: Optional path to the dotfiles source directory.
        """
        self.config_path = self.find_config_path(config, source)
        self.default_path: Optional[Path] = self._resolve_default_path()
        self.settings = self._load_settings()

        if source:
            self.settings["dotfiles"] = source

        if not self.settings["dotfiles"]:
            print(
                "A source to your dotfiles cannot be identified. Pass in a source or config file."
            )
            sys.exit()

    def _resolve_default_path(self) -> Optional[Path]:
        """Resolve the default configuration file path."""
        try:
            default_traversable = resources.files("doti") / "defaults.yaml"
            default_path = Path(str(default_traversable))
            return default_path if default_path.is_file() else None
        except (ModuleNotFoundError, FileNotFoundError):
            return None

    def find_config_path(
        self, config: Optional[str], source: Optional[str]
    ) -> Optional[Path]:
        """
        Locate the configuration file.

        Searches in the following order:
        1. Explicit config path
        2. Inside source directory
        3. User home directory (~/.config/doti/settings.yaml)

        Args:
            config: Explicit config file path.
            source: Dotfiles source directory path.

        Returns:
            Path to configuration file if found, None otherwise.
        """
        config_location = ".config/doti/settings.yaml"

        def get_candidates():
            if config:
                yield Path(config)

            if source:
                src = Path(source)
                yield src / config_location
                yield src / config_location.lstrip(".")

            yield Path("~") / config_location

        for candidate in get_candidates():
            path = candidate.expanduser().resolve()
            if path.is_file():
                return path

        return None

    def _load_settings(self) -> Dict[str, Any]:
        """
        Load and merge settings from default and user configuration files.

        Returns:
            Merged settings dictionary with user values overriding defaults.
        """
        user = _load_yaml(self.config_path) if self.config_path else {}
        defaults = _load_yaml(self.default_path, strict=True)

        defaults.update(user)

        return defaults

    @cached_property
    def source(self) -> Path:
        """Get the path to the dotfiles source directory."""
        return Path(self.settings["dotfiles"]).expanduser().resolve()

    @cached_property
    def target(self) -> Path:
        """Get the path to the target (home) directory."""
        return Path(self.settings["home"]).expanduser().resolve()

    @cached_property
    def link_icon(self) -> str:
        """Get the icon used to indicate a linked file."""
        return self.settings["link_icon"]

    @cached_property
    def confirm_changes(self) -> bool:
        """Get whether to confirm changes before applying."""
        return self.settings["confirm_changes"]

    @cached_property
    def backup_suffix(self) -> str:
        """Get the suffix used for backup files."""
        return self.settings["backup_suffix"]

    @cached_property
    def backup_icon(self) -> str:
        """Get the icon used to indicate a backup exists."""
        return self.settings["backup_icon"]

    @cached_property
    def add_dot(self) -> bool:
        """Get whether to add a dot prefix to filenames in target."""
        return self.settings["add_dot"]
