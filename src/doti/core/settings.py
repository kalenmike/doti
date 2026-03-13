from pathlib import Path
from functools import cached_property
import yaml
from importlib import resources
import sys


class SettingsManager:
    def __init__(self, config=None, source=None):

        self.config_path = self.find_config_path(config, source)
        self.default_path = resources.files("doti") / "defaults.yaml"
        self.settings = self._load_settings()

        if source:
            # Ensure source is being used
            self.settings["dotfiles"] = source

        if not self.settings["dotfiles"]:
            print(
                "A source to your dotfiles cannot be identified. Pass in a source or config file."
            )
            sys.exit()

    def find_config_path(self, config: str | None, source: str | None):
        config_location = ".config/doti/settings.yaml"

        if config:
            # Use provided config file
            tmp_path = Path(config).expanduser().resolve()
            if tmp_path.is_file():
                return tmp_path

        if source:
            # Look inside source
            tmp_path = Path(source) / config_location
            tmp_path = tmp_path.expanduser().resolve()
            if tmp_path.is_file():
                return tmp_path

            # Check without prefixed dot
            tmp_path = Path(source) / config_location.removeprefix(".")
            tmp_path = tmp_path.expanduser().resolve()
            if tmp_path.is_file():
                return tmp_path

        # Look in normal location
        tmp_path = Path("~") / config_location
        tmp_path = tmp_path.expanduser().resolve()
        if tmp_path.is_file():
            return tmp_path

        # No config
        return None

    def _load_settings(self):
        user = self._load_yaml(self.config_path) if self.config_path else {}
        defaults = self._load_yaml(self.default_path)

        # Overwrite defaults with user preferences
        defaults.update(user)

        return defaults

    def _load_yaml(self, path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _get_str_default(self, key, default=""):
        if self.settings is None:
            return default

        return self.settings.get(key, default)

    def _get_bool_default(self, key, default=False):
        if self.settings is None:
            return default

        return self.settings.get(key, default)

    @cached_property
    def source(self):
        return Path(self._get_str_default("dotfiles")).expanduser().resolve()

    @cached_property
    def target(self):
        return Path(self._get_str_default("home", "~")).expanduser().resolve()

    @cached_property
    def link_icon(self):
        return self._get_str_default("link_icon", "✔")

    @cached_property
    def confirm_changes(self):
        return self._get_bool_default("confirm_changes", True)

    @cached_property
    def backup_suffix(self):
        return self._get_str_default("backup_suffix", ".bkp")

    @cached_property
    def backup_icon(self):
        return self._get_str_default("backup_icon", "⊚")

    @cached_property
    def add_dot(self):
        return self._get_bool_default("add_dot", True)
