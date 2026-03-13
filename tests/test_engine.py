"""Tests for doti.core.engine module."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from doti.core.engine import Doti
from doti.core.settings import SettingsManager
from doti.utils.data import ConfigNode, ChangeType


class TestDoti:
    """Tests for the Doti class."""

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

    def test_doti_initialization(self, settings):
        """Test Doti engine initializes correctly."""
        doti = Doti(settings)
        assert doti.cfg is not None
        assert isinstance(doti.tree, dict)
        assert isinstance(doti.allowed_dirs, set)

    def test_exists_file(self, temp_dirs):
        """Test exists returns True for existing file."""
        source, target = temp_dirs
        test_file = source / "test.txt"
        test_file.write_text("content")

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        assert doti.exists(test_file) is True

    def test_exists_symlink(self, temp_dirs):
        """Test exists returns True for symlink."""
        source, target = temp_dirs
        test_file = source / "test.txt"
        test_file.write_text("content")
        link = target / "link"
        link.symlink_to(test_file)

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        assert doti.exists(link) is True

    def test_exists_nonexistent(self, temp_dirs):
        """Test exists returns False for nonexistent path."""
        source, target = temp_dirs

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        assert doti.exists(source / "nonexistent") is False

    def test_has_symlink_same_path_raises_error(self, temp_dirs):
        """Test has_symlink raises error when source and target are same."""
        source, target = temp_dirs

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        with pytest.raises(ValueError, match="Source and Target cannot be the same"):
            doti.has_symlink(source, source)

    def test_has_symlink_true(self, temp_dirs):
        """Test has_symlink returns True when target is symlink to source."""
        source, target = temp_dirs
        test_file = source / "test.txt"
        test_file.write_text("content")
        link = target / "test.txt"
        link.symlink_to(test_file)

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        assert doti.has_symlink(test_file, link) is True

    def test_has_symlink_false(self, temp_dirs):
        """Test has_symlink returns False when not a symlink."""
        source, target = temp_dirs
        source_file = source / "source.txt"
        source_file.write_text("content")
        target_file = target / "target.txt"
        target_file.write_text("different")

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        assert doti.has_symlink(source_file, target_file) is False

    def test_get_backup_path_file(self, temp_dirs):
        """Test backup path for file."""
        source, target = temp_dirs

        config = source / "config.yaml"
        config.write_text("dotfiles: .\nhome: .\n")
        settings = SettingsManager(config=str(config), source=str(source))
        doti = Doti(settings)

        backup = doti.get_backup_path(source / "test.txt")
        assert backup.name == "test.txt.bkp"

    def test_get_backup_path_hidden_file(self, temp_dirs):
        """Test backup path for hidden file."""
        source, target = temp_dirs

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        backup = doti.get_backup_path(source / ".bashrc")
        assert backup.name == ".bashrc.bkp"

    def test_get_backup_path_directory(self, temp_dirs):
        """Test backup path for directory."""
        source, target = temp_dirs

        settings = SettingsManager(config=None, source=str(source))
        doti = Doti(settings)

        backup = doti.get_backup_path(source / ".config")
        assert backup.name == ".config.bkp"

    def test_get_dot_prefix_add_dot(self, temp_dirs):
        """Test get_dot_prefix adds dot when add_dot is True."""
        source, target = temp_dirs

        config = source / "config.yaml"
        config.write_text("dotfiles: .\nhome: .\nadd_dots: true\n")

        settings = SettingsManager(config=str(config), source=str(source))
        doti = Doti(settings)

        assert doti.get_dot_prefix("bashrc") == "."
        assert doti.get_dot_prefix(".bashrc") == ""

    def test_get_dot_prefix_no_add_dot(self, temp_dirs):
        """Test get_dot_prefix doesn't add dot when add_dot is False."""
        source, target = temp_dirs

        config = source / "config.yaml"
        config.write_text("dotfiles: .\nhome: .\nadd_dot: false\n")

        settings = SettingsManager(config=str(config), source=str(source))
        doti = Doti(settings)

        assert doti.get_dot_prefix("bashrc") == ""
        assert doti.get_dot_prefix(".bashrc") == ""

    def test_get_label(self, temp_dirs):
        """Test get_label generates correct labels."""
        source, target = temp_dirs

        config = source / "config.yaml"
        config.write_text("dotfiles: .\nhome: .\n")
        settings = SettingsManager(config=str(config), source=str(source))
        doti = Doti(settings)

        assert doti.get_label("test") == "test"
        assert doti.get_label("test", exists=True) == "test ↗"
        assert doti.get_label("test", has_backup=True) == "test ⊚"
        assert doti.get_label("test", exists=True, has_backup=True) == "test ↗ ⊚"


class TestDotiTreeOperations:
    """Tests for Doti tree operations."""

    @pytest.fixture
    def populated_doti(self):
        """Create Doti with populated tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"

            source.mkdir()
            target.mkdir()

            (source / ".bashrc").write_text("rc content")
            (source / ".config").mkdir()
            (source / ".config" / "nvim").write_text("nvim config")

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))
            doti = Doti(settings)

            yield doti, source, target

    def test_filter_tree_returns_dict(self, populated_doti):
        """Test filter_tree returns a dictionary."""
        doti, _, _ = populated_doti
        result = doti.filter_tree(lambda n: n.in_source)
        assert isinstance(result, dict)

    def test_get_source_only(self, populated_doti):
        """Test get_source_only returns nodes from source."""
        doti, _, _ = populated_doti
        result = doti.get_source_only()

        assert ".bashrc" in result
        assert ".config" in result
        assert "nvim" in result[".config"].children

    def test_get_target_only_empty(self, populated_doti):
        """Test get_target_only returns empty when target is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"

            source.mkdir()
            target.mkdir()

            (source / ".bashrc").write_text("rc content")

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            settings = SettingsManager(config=str(config), source=str(source))
            doti = Doti(settings)

            result = doti.get_target_only()
            assert len(result) == 0

    def test_flatten_tree(self, populated_doti):
        """Test flatten_tree returns list of all nodes."""
        doti, _, _ = populated_doti
        source_only = doti.get_source_only()
        flat = doti.flatten_tree(source_only)

        assert len(flat) >= 3
        names = [n.name for n in flat]
        assert ".bashrc" in names
        assert ".config" in names


class TestDotiPlanCalculation:
    """Tests for Doti plan calculation."""

    @pytest.fixture
    def doti_with_symlink(self):
        """Create Doti with a symlink already in place."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"

            source.mkdir()
            target.mkdir()

            (source / ".bashrc").write_text("rc content")

            target_file = target / ".bashrc"
            target_file.symlink_to(source / ".bashrc")

            config = source / "config.yaml"
            config.write_text("dotfiles: .\nhome: .\n")

            settings = SettingsManager(config=str(config), source=str(source))
            doti = Doti(settings)

            yield doti, source, target

    def test_calculate_plan_add_new(self, doti_with_symlink):
        """Test calculating plan to add new symlinks."""
        doti, source, _ = doti_with_symlink

        source_only = doti.get_source_only()
        selected = list(source_only.values())

        plan = doti.calculate_plan(source_only, selected)

        add_changes = [n for n in plan if n.change == ChangeType.ADD]
        assert len(add_changes) >= 1

    def test_calculate_plan_remove_existing(self, doti_with_symlink):
        """Test calculating plan to remove existing symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"

            source.mkdir()
            target.mkdir()

            (source / ".bashrc").write_text("rc content")

            target_file = target / ".bashrc"
            target_file.symlink_to(source / ".bashrc")

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            settings = SettingsManager(config=str(config), source=str(source))
            doti = Doti(settings)

            source_only = doti.get_source_only()

            plan = doti.calculate_plan(source_only, [])
            remove_changes = [n for n in plan if n.change == ChangeType.REMOVE]
            assert len(remove_changes) >= 1

    def test_calculate_plan_no_change(self, doti_with_symlink):
        """Test calculating plan with no changes."""
        doti, source, _ = doti_with_symlink

        source_only = doti.get_source_only()
        selected = list(source_only.values())

        plan = doti.calculate_plan(source_only, selected)

        for node in plan:
            assert node.change != ChangeType.REMOVE
