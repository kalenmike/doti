"""Tests for doti.main module - user flow integration tests."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from doti.main import main, handle_manage, handle_migrate
from doti.core.settings import SettingsManager
from doti.core.engine import Doti
from doti.utils.data import ConfigNode, ChangeType


class TestMainEntryPoint:
    """Tests for the main CLI entry point."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary source and target directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            yield source, target, config

    def test_main_manage_action(self, temp_dirs, capsys):
        """Test main entry point with manage action."""
        source, target, config = temp_dirs

        (source / ".bashrc").write_text("bash content")

        test_args = ["doti", "manage", "-c", str(config)]
        with patch.object(sys, "argv", test_args):
            with patch("doti.main.handle_manage") as mock_handle:
                main()
                mock_handle.assert_called_once_with(str(config), None)

    def test_main_migrate_action(self, temp_dirs, capsys):
        """Test main entry point with migrate action."""
        source, target, config = temp_dirs

        test_args = ["doti", "migrate", "-c", str(config)]
        with patch.object(sys, "argv", test_args):
            with patch("doti.main.handle_migrate") as mock_handle:
                main()
                mock_handle.assert_called_once_with(str(config), None)

    def test_main_with_source_flag(self, temp_dirs, capsys):
        """Test main entry point with source flag."""
        source, target, config = temp_dirs

        test_args = ["doti", "manage", "-s", str(source)]
        with patch.object(sys, "argv", test_args):
            with patch("doti.main.handle_manage") as mock_handle:
                main()
                mock_handle.assert_called_once_with(None, str(source))


class TestHandleManage:
    """Tests for the handle_manage function."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary source and target directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            (source / ".bashrc").write_text("bash content")
            (source / ".vimrc").write_text("vim content")

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            yield source, target, config

    def test_handle_manage_cancelled(self, temp_dirs, capsys):
        """Test handle_manage when user cancels selection."""
        source, target, config = temp_dirs

        with patch("doti.main.TUI") as MockTUI:
            mock_tui_instance = MagicMock()
            mock_tui_instance.render.return_value = None
            MockTUI.return_value = mock_tui_instance

            handle_manage(str(config), None)

            captured = capsys.readouterr()
            assert "Selection cancelled" in captured.out

    def test_handle_manage_with_selection_confirm_true(self, temp_dirs, capsys):
        """Test handle_manage applies changes when confirmed."""
        source, target, config = temp_dirs

        with patch("doti.main.TUI") as MockTUI:
            mock_tui_instance = MagicMock()
            mock_tui_instance.render.return_value = [
                ConfigNode(
                    name=".bashrc",
                    relative_path=Path(".bashrc"),
                    in_source=True,
                )
            ]
            mock_tui_instance.confirm.return_value = True
            MockTUI.return_value = mock_tui_instance

            handle_manage(str(config), None)

            mock_tui_instance.print_action_plan.assert_called_once()
            mock_tui_instance.confirm.assert_called_once_with("Apply Changes?")

    def test_handle_manage_with_selection_confirm_false(self, temp_dirs, capsys):
        """Test handle_manage does not apply when not confirmed."""
        source, target, config = temp_dirs

        with patch("doti.main.TUI") as MockTUI:
            mock_tui_instance = MagicMock()
            mock_tui_instance.render.return_value = [
                ConfigNode(
                    name=".bashrc",
                    relative_path=Path(".bashrc"),
                    in_source=True,
                )
            ]
            mock_tui_instance.confirm.return_value = False
            MockTUI.return_value = mock_tui_instance

            handle_manage(str(config), None)

            mock_tui_instance.print_action_plan.assert_called_once()
            mock_tui_instance.confirm.assert_called_once_with("Apply Changes?")

    def test_handle_manage_without_confirmation(self, temp_dirs, capsys):
        """Test handle_manage applies changes without confirmation when disabled."""
        source, target, config = temp_dirs

        config.write_text(
            f"dotfiles: {source}\nhome: {target}\nconfirm_changes: false\n"
        )

        with patch("doti.main.TUI") as MockTUI:
            mock_tui_instance = MagicMock()
            mock_tui_instance.render.return_value = [
                ConfigNode(
                    name=".bashrc",
                    relative_path=Path(".bashrc"),
                    in_source=True,
                )
            ]
            MockTUI.return_value = mock_tui_instance

            handle_manage(str(config), None)

            mock_tui_instance.confirm.assert_not_called()


class TestHandleMigrate:
    """Tests for the handle_migrate function."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary source and target directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            yield source, target, config

    def test_handle_migrate_no_untracked(self, temp_dirs, capsys):
        """Test handle_migrate when no files exist to migrate."""
        source, target, config = temp_dirs

        handle_migrate(str(config), None)

        captured = capsys.readouterr()
        assert "No files found" in captured.out


class TestFullUserFlow:
    """Integration tests for full user workflows."""

    @pytest.fixture
    def setup_test_env(self):
        """Create a complete test environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "dotfiles"
            target = Path(tmpdir) / "home"
            source.mkdir()
            target.mkdir()

            (source / ".bashrc").write_text("export PATH=...\n")
            (source / ".config").mkdir()
            (source / ".config" / "nvim").mkdir()
            (source / ".config" / "nvim" / "init.lua").write_text(
                "vim.g.mapleader = ' '\n"
            )

            config = source / "config.yaml"
            config.write_text(f"dotfiles: {source}\nhome: {target}\n")

            yield source, target, config

    def test_full_flow_get_source_files(self, setup_test_env):
        """Test getting source files from the main flow."""
        source, target, config = setup_test_env

        cfg = SettingsManager(config=str(config), source=str(source))
        doti = Doti(cfg)

        source_files = doti.get_source_only()

        assert len(source_files) >= 1

    def test_full_flow_create_symlink(self, setup_test_env):
        """Test creating a symlink through the full flow."""
        source, target, config = setup_test_env

        cfg = SettingsManager(config=str(config), source=str(source))
        doti = Doti(cfg)

        source_files = doti.get_source_only()
        flat_files = doti.flatten_tree(source_files)

        node = flat_files[0]
        node.change = ChangeType.ADD

        doti.process_plan([node])

        expected_link = target / node.relative_path
        assert expected_link.is_symlink()
        assert expected_link.resolve() == source / node.relative_path

    def test_full_flow_remove_symlink(self, setup_test_env):
        """Test removing a symlink through the full flow."""
        source, target, config = setup_test_env

        source_file = source / ".bashrc"
        target_link = target / ".bashrc"
        target_link.symlink_to(source_file)

        cfg = SettingsManager(config=str(config), source=str(source))
        doti = Doti(cfg)

        source_files = doti.get_source_only()

        plan = doti.calculate_plan(source_files, [])
        remove_nodes = [n for n in plan if n.change == ChangeType.REMOVE]

        doti.process_plan(remove_nodes)

        assert not target_link.exists()
        assert not target_link.is_symlink()
