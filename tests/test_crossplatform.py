"""Cross-platform compatibility tests."""

import sys
import pytest
from pathlib import Path, PurePosixPath, PureWindowsPath


class TestPathHandling:
    """Tests for cross-platform path handling."""

    def test_path_works_with_different_separators(self):
        """Test Path handles various path formats correctly."""
        p = Path("home/user/.config")
        assert p.parts == ("home", "user", ".config")

    def test_path_with_forward_slash(self):
        """Test Path handles forward slashes."""
        p = Path("source/dotfiles")
        assert p.name == "dotfiles"

    def test_relative_path_cross_platform(self):
        """Test relative path works cross-platform."""
        p = Path(".config/nvim/init.lua")
        assert p.parent == PurePosixPath(".config/nvim")
        assert p.name == "init.lua"

    def test_path_join_works(self):
        """Test Path join operations."""
        source = Path("/home/user/dotfiles")
        rel_path = Path(".bashrc")
        result = source / rel_path
        assert result == Path("/home/user/dotfiles/.bashrc")


class TestPlatformDetection:
    """Tests for platform-specific behavior."""

    def test_platform_is_detected(self):
        """Test sys.platform is available."""
        assert sys.platform in ("linux", "darwin", "win32", "cygwin", "freebsd")

    def test_path_separator_is_platform_specific(self):
        """Test Path uses correct separator for platform."""
        p = Path("a", "b", "c")
        if sys.platform == "win32":
            assert "\\" in str(p) or ":" in str(p)
        else:
            assert "/" in str(p)


class TestSymlinkCrossPlatform:
    """Tests for cross-platform symlink behavior."""

    def test_symlink_creation_on_current_platform(self, tmp_path):
        """Test symlink can be created on current platform."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        link = tmp_path / "link.txt"

        try:
            link.symlink_to(source)
            assert link.is_symlink()
            assert link.resolve() == source.resolve()
        except (OSError, NotImplementedError) as e:
            pytest.skip(f"Symlinks not supported on this platform: {e}")

    def test_directory_symlink_on_current_platform(self, tmp_path):
        """Test directory symlink can be created on current platform."""
        source_dir = tmp_path / "source_dir"
        source_dir.mkdir()

        link_dir = tmp_path / "link_dir"

        try:
            link_dir.symlink_to(source_dir)
            assert link_dir.is_symlink()
            assert link_dir.is_dir()
        except (OSError, NotImplementedError) as e:
            pytest.skip(f"Directory symlinks not supported: {e}")


class TestYamlConfigCrossPlatform:
    """Tests for YAML config cross-platform compatibility."""

    def test_yaml_paths_work_cross_platform(self, tmp_path):
        """Test YAML config with paths works on any platform."""
        import yaml

        config = {
            "dotfiles": str(tmp_path / "dotfiles"),
            "home": str(tmp_path / "home"),
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with open(config_file, "r") as f:
            loaded = yaml.safe_load(f)

        assert loaded["dotfiles"] is not None
        assert loaded["home"] is not None

        loaded_path = Path(loaded["dotfiles"])
        assert loaded_path.is_absolute()


class TestQuestionaryCrossPlatform:
    """Tests for questionary TUI cross-platform behavior."""

    def test_questionary_imports(self):
        """Test questionary can be imported."""
        import questionary

        assert hasattr(questionary, "checkbox")
        assert hasattr(questionary, "confirm")

    def test_prompt_toolkit_styles(self):
        """Test prompt_toolkit styles work."""
        from prompt_toolkit.styles import Style

        style = Style([("qmark", "hidden")])
        assert style is not None


class TestWindowsCompatibility:
    """Tests specific to Windows compatibility concerns."""

    def test_backup_path_windows_compatible(self):
        """Test backup path generation works on Windows."""
        from doti.core.engine import Doti
        from doti.core.settings import SettingsManager
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            settings = SettingsManager(config=str(config), source=str(source))
            doti = Doti(settings)

            backup = doti.get_backup_path(source / "test.txt")
            assert backup.suffix == ".bkp"

    def test_hidden_file_detection(self):
        """Test hidden file detection works cross-platform."""
        p = Path(".bashrc")
        assert p.name.startswith(".")

        p2 = Path("normal.txt")
        assert not p2.name.startswith(".")

    def test_path_resolve_works(self):
        """Test Path.resolve() works cross-platform."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            resolved = p.resolve()
            assert resolved.is_absolute()
            assert resolved.exists()
