"""Tests for doti.utils.data module."""

from pathlib import Path
import pytest
from doti.utils.data import ConfigNode, ChangeType, ConfigTree, NodeOrigin


class TestNodeOrigin:
    """Tests for the NodeOrigin enum."""

    def test_node_origin_values(self):
        """Test NodeOrigin enum has correct values."""
        assert NodeOrigin.SOURCE is not None
        assert NodeOrigin.TARGET is not None

    def test_node_origin_members(self):
        """Test NodeOrigin enum has expected members."""
        assert hasattr(NodeOrigin, "SOURCE")
        assert hasattr(NodeOrigin, "TARGET")


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


class TestConfigTree:
    """Tests for the ConfigTree class."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary source and target directories."""
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()
        return source, target

    @pytest.fixture
    def config_tree(self, temp_dirs):
        """Create a ConfigTree with test data."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)

        source_file = source / ".bashrc"
        source_file.write_text("")
        source_dir = source / ".config"
        source_dir.mkdir()

        target_file = target / ".bashrc"
        target_file.write_text("")
        target_new = target / ".zshrc"
        target_new.write_text("")

        tree.create_and_add_node(".bashrc", source_file, NodeOrigin.SOURCE)
        tree.create_and_add_node(".config", source_dir, NodeOrigin.SOURCE)
        tree.create_and_add_node(".bashrc", target_file, NodeOrigin.TARGET)
        tree.create_and_add_node(".zshrc", target_new, NodeOrigin.TARGET)

        return tree

    def test_config_tree_creation(self, temp_dirs):
        """Test ConfigTree can be created."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)
        assert tree.origins[NodeOrigin.SOURCE] == source
        assert tree.origins[NodeOrigin.TARGET] == target

    def test_get_tree_empty(self, temp_dirs):
        """Test get_tree returns empty dict initially."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)
        assert tree.get_tree() == {}

    def test_add_node_source(self, config_tree):
        """Test adding a node from source."""
        assert ".bashrc" in config_tree.source_keys
        assert ".config" in config_tree.source_keys

    def test_add_node_target(self, config_tree):
        """Test adding a node from target."""
        assert ".bashrc" in config_tree.target_keys
        assert ".zshrc" in config_tree.target_keys

    def test_get_node_existing(self, config_tree):
        """Test getting an existing node."""
        node = config_tree.get_node(".bashrc")
        assert node is not None
        assert node.name == ".bashrc"

    def test_get_node_not_existing(self, config_tree):
        """Test getting a non-existing node returns None."""
        node = config_tree.get_node(".nonexistent")
        assert node is None

    def test_create_node(self, temp_dirs):
        """Test creating a node."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)
        source_file = source / ".bashrc"
        source_file.write_text("")

        node = tree.create_node(".bashrc", source_file, NodeOrigin.SOURCE)
        assert node.name == ".bashrc"
        assert node.relative_path == Path(".bashrc")
        assert node.in_source is True
        assert node.in_target is False

    def test_create_and_add_node(self, temp_dirs):
        """Test creating and adding a node."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)
        source_file = source / ".bashrc"
        source_file.write_text("")

        node = tree.create_and_add_node(".bashrc", source_file, NodeOrigin.SOURCE)
        assert node is not None
        assert ".bashrc" in tree.source_keys

    def test_get_relative_path(self, temp_dirs):
        """Test getting relative path."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)
        source_file = source / ".config" / "shell" / "aliases"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("")

        rel_path = tree.get_relative_path(source_file, NodeOrigin.SOURCE)
        assert rel_path == Path(".config/shell/aliases")

    def test_create_new_tree(self, temp_dirs):
        """Test creating a new empty tree with same origins."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)
        new_tree = tree.create_new_tree()

        assert new_tree.origins[NodeOrigin.SOURCE] == source
        assert new_tree.origins[NodeOrigin.TARGET] == target
        assert new_tree.get_tree() == {}

    def test_get_source_tree(self, config_tree):
        """Test getting source-only tree (files only in source)."""
        source_tree = config_tree.get_source_tree()
        assert ".config" in source_tree.source_keys
        assert ".bashrc" not in source_tree.source_keys

    def test_get_target_tree(self, config_tree):
        """Test getting target-only tree (files only in target)."""
        target_tree = config_tree.get_target_tree()
        assert ".zshrc" in target_tree.target_keys
        assert ".bashrc" not in target_tree.target_keys

    def test_get_filtered_tree(self, config_tree):
        """Test filtering tree by keys."""
        filtered = config_tree.get_filtered_tree({".bashrc"}, NodeOrigin.SOURCE)
        assert ".bashrc" in filtered.source_keys
        assert ".config" not in filtered.source_keys

    def test_get_filtered_tree_with_filter_func(self, config_tree):
        """Test filtering tree with filter function."""
        source_file = config_tree.origins[NodeOrigin.SOURCE] / ".bashrc"
        node = config_tree.get_node(".bashrc")
        node.is_symlink = True

        filtered = config_tree.get_filtered_tree(
            config_tree.source_keys, NodeOrigin.SOURCE, lambda n: n.is_symlink
        )
        assert ".bashrc" in filtered.source_keys
        assert ".config" not in filtered.source_keys

    def test_get_target_hard_tree(self, temp_dirs):
        """Test getting symlink-only tree from target."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)

        source_file = source / ".bashrc"
        source_file.write_text("")
        target_file = target / ".bashrc"
        target_file.symlink_to(source_file)

        target_file_new = target / ".zshrc"
        target_file_new.symlink_to(source_file)

        target_file_regular = target / ".profile"
        target_file_regular.write_text("")

        tree.create_and_add_node(".bashrc", source_file, NodeOrigin.SOURCE)
        tree.create_and_add_node(".bashrc", target_file, NodeOrigin.TARGET)
        tree.create_and_add_node(".zshrc", target_file_new, NodeOrigin.TARGET)
        tree.create_and_add_node(".profile", target_file_regular, NodeOrigin.TARGET)

        zshrc_node = tree.get_node(".zshrc")
        assert zshrc_node is not None
        zshrc_node.is_symlink = True

        profile_node = tree.get_node(".profile")
        assert profile_node is not None
        profile_node.is_symlink = False

        hard_tree = tree.get_target_hard_tree()
        assert ".zshrc" in hard_tree.target_keys
        assert ".profile" not in hard_tree.target_keys

    def test_get_children(self, temp_dirs):
        """Test getting direct children of a parent node."""
        source, target = temp_dirs
        tree = ConfigTree(source, target)

        tree.add_node(
            ConfigNode(name=".config", relative_path=Path(".config"), is_dir=True),
            NodeOrigin.SOURCE,
        )
        tree.add_node(
            ConfigNode(
                name=".config/shell", relative_path=Path(".config/shell"), is_dir=True
            ),
            NodeOrigin.SOURCE,
        )
        tree.add_node(
            ConfigNode(
                name=".config/shell/aliases",
                relative_path=Path(".config/shell/aliases"),
            ),
            NodeOrigin.SOURCE,
        )
        tree.add_node(
            ConfigNode(
                name=".config/nvim", relative_path=Path(".config/nvim"), is_dir=True
            ),
            NodeOrigin.SOURCE,
        )

        children = tree.get_children(".config")
        assert len(children) == 2
        child_names = {c.name for c in children}
        assert ".config/shell" in child_names
        assert ".config/nvim" in child_names

    def test_source_and_target_constants(self):
        """Test SOURCE and TARGET class attributes."""
        assert ConfigTree.SOURCE == NodeOrigin.SOURCE
        assert ConfigTree.TARGET == NodeOrigin.TARGET
