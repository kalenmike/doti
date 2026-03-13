"""Tests for doti.utils.data module."""

from pathlib import Path
import pytest
from doti.utils.data import ConfigNode, ChangeType


class TestChangeType:
    """Tests for the ChangeType enum."""

    def test_change_type_values(self):
        """Test ChangeType enum has correct values."""
        assert ChangeType.ADD.value == "ADD"
        assert ChangeType.REMOVE.value == "REMOVE"
        assert ChangeType.KEEP.value == "KEEP"

    def test_change_type_members(self):
        """Test ChangeType enum has all expected members."""
        assert hasattr(ChangeType, "ADD")
        assert hasattr(ChangeType, "REMOVE")
        assert hasattr(ChangeType, "KEEP")


class TestConfigNode:
    """Tests for the ConfigNode dataclass."""

    def test_config_node_creation(self):
        """Test ConfigNode can be created with required fields."""
        node = ConfigNode(
            name=".bashrc",
            relative_path=Path(".bashrc"),
        )
        assert node.name == ".bashrc"
        assert node.relative_path == Path(".bashrc")
        assert node.is_dir is False
        assert node.in_source is False
        assert node.in_target is False
        assert node.is_symlink is False
        assert node.has_backup is False
        assert node.change is None
        assert node.children == {}

    def test_config_node_with_all_fields(self):
        """Test ConfigNode with all fields specified."""
        child = ConfigNode(
            name="aliases",
            relative_path=Path(".config/shell/aliases"),
        )
        node = ConfigNode(
            name=".config",
            relative_path=Path(".config"),
            is_dir=True,
            in_source=True,
            in_target=True,
            is_symlink=True,
            has_backup=True,
            change=ChangeType.KEEP,
            children={"aliases": child},
        )
        assert node.name == ".config"
        assert node.is_dir is True
        assert node.in_source is True
        assert node.in_target is True
        assert node.is_symlink is True
        assert node.has_backup is True
        assert node.change == ChangeType.KEEP
        assert "aliases" in node.children
        assert node.children["aliases"].name == "aliases"

    def test_config_node_children_default_empty(self):
        """Test children defaults to empty dict."""
        node = ConfigNode(name="test", relative_path=Path("test"))
        assert node.children == {}

    def test_config_node_change_type_assignment(self):
        """Test change field accepts ChangeType values."""
        node = ConfigNode(name="test", relative_path=Path("test"))
        node.change = ChangeType.ADD
        assert node.change == ChangeType.ADD

        node.change = ChangeType.REMOVE
        assert node.change == ChangeType.REMOVE
