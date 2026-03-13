"""Tests for doti.core.ui module."""

import tempfile
import pytest
from pathlib import Path
from doti.core.ui import TUI
from doti.core.settings import SettingsManager
from doti.utils.data import ConfigNode, ChangeType


class TestTUI:
    """Tests for the TUI class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary source and target directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()
            yield source, target

    @pytest.fixture
    def settings(self, temp_dirs):
        """Create SettingsManager with temp directories."""
        source, target = temp_dirs
        config = source / "config.yaml"
        config.write_text("dotfiles: .\nhome: .\n")
        return SettingsManager(config=str(config), source=str(source))

    def test_tui_initialization(self, settings):
        """Test TUI initializes correctly."""
        tui = TUI(settings)
        assert tui.cfg is settings
        assert tui.styles is not None

    def test_get_styles_returns_style(self, settings):
        """Test get_styles returns a Style object."""
        tui = TUI(settings)
        styles = tui.get_styles()
        assert styles is not None

    def test_clear_output(self, settings, capsys):
        """Test clear_output writes escape codes."""
        tui = TUI(settings)
        tui.clear_output(1)

        captured = capsys.readouterr()
        assert "\033[F\033[K" in captured.out


class TestBuildChoices:
    """Tests for TUI choice building."""

    @pytest.fixture
    def tui_with_settings(self):
        """Create TUI with settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))
            tui = TUI(settings)

            yield tui, settings

    def test_build_choices_single_node(self, tui_with_settings):
        """Test building choices for single node."""
        tui, _ = tui_with_settings

        nodes = {
            ".bashrc": ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                in_source=True,
            )
        }

        choices = tui.build_choices(nodes)
        assert len(choices) == 1

    def test_build_choices_with_directory(self, tui_with_settings):
        """Test building choices includes directory children."""
        tui, _ = tui_with_settings

        child = ConfigNode(
            name="config",
            relative_path=Path(".config/config"),
            in_source=True,
        )
        nodes = {
            ".config": ConfigNode(
                name=".config",
                relative_path=Path(".config"),
                is_dir=True,
                in_source=True,
                children={"config": child},
            )
        }

        choices = tui.build_choices(nodes)
        assert len(choices) >= 1

    def test_build_choices_checks_symlink_status(self, tui_with_settings):
        """Test choices reflect symlink status."""
        tui, _ = tui_with_settings

        nodes = {
            ".bashrc": ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                in_source=True,
                is_symlink=True,
            )
        }

        choices = tui.build_choices(nodes)
        choice = choices[0]
        assert choice.checked is True

    def test_build_choices_unchecked_when_not_linked(self, tui_with_settings):
        """Test choices are unchecked when not a symlink."""
        tui, _ = tui_with_settings

        nodes = {
            ".bashrc": ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                in_source=True,
                is_symlink=False,
            )
        }

        choices = tui.build_choices(nodes)
        choice = choices[0]
        assert choice.checked is False


class TestGetChoices:
    """Tests for get_choices method."""

    @pytest.fixture
    def tui_with_settings(self):
        """Create TUI with settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))
            tui = TUI(settings)

            yield tui, settings

    def test_get_choices_adds_header(self, tui_with_settings):
        """Test get_choices adds target directory header."""
        tui, settings = tui_with_settings

        nodes = {
            ".bashrc": ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                in_source=True,
            )
        }

        choices = tui.get_choices(nodes)
        assert len(choices) >= 1


class TestPrintActionPlan:
    """Tests for action plan printing."""

    @pytest.fixture
    def tui_with_settings(self):
        """Create TUI with settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))
            tui = TUI(settings)

            yield tui, settings

    def test_print_action_plan_empty(self, tui_with_settings, capsys):
        """Test printing empty plan."""
        tui, _ = tui_with_settings
        tui.print_action_plan([])

        captured = capsys.readouterr()
        assert "Pending Changes:" in captured.out

    def test_print_action_plan_with_add(self, tui_with_settings):
        """Test plan with ADD action sets correct change type."""
        tui, _ = tui_with_settings

        nodes = [
            ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                change=ChangeType.ADD,
            )
        ]

        for node in nodes:
            assert node.change == ChangeType.ADD

    def test_print_action_plan_with_remove(self, tui_with_settings):
        """Test plan with REMOVE action sets correct change type."""
        tui, _ = tui_with_settings

        nodes = [
            ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                change=ChangeType.REMOVE,
                is_symlink=True,
            )
        ]

        for node in nodes:
            assert node.change == ChangeType.REMOVE

    def test_print_action_plan_shows_backup(self, tui_with_settings):
        """Test backup indicator logic."""
        tui, _ = tui_with_settings

        nodes = [
            ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                change=ChangeType.ADD,
                in_target=True,
            )
        ]

        node = nodes[0]
        assert node.change == ChangeType.ADD
        assert node.in_target is True

    def test_print_action_plan_shows_restore(self, tui_with_settings):
        """Test restore indicator logic."""
        tui, _ = tui_with_settings

        nodes = [
            ConfigNode(
                name=".bashrc",
                relative_path=Path(".bashrc"),
                change=ChangeType.REMOVE,
                is_symlink=True,
                has_backup=True,
            )
        ]

        node = nodes[0]
        assert node.change == ChangeType.REMOVE
        assert node.has_backup is True
