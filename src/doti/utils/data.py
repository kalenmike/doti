"""Data structures for Doti configuration management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, List
from enum import Enum, auto


class ChangeType(Enum):
    """Represents the type of change to be applied to a configuration node."""

    ADD = "ADD"
    REMOVE = "REMOVE"
    KEEP = "KEEP"


class NodeOrigin(Enum):
    """Represents the origin of a configuration node (source or target)."""

    SOURCE = auto()
    TARGET = auto()


@dataclass
class ConfigNode:
    """
    Represents a single configuration file or directory in the Doti tree.

    Attributes:
        name: The filename or directory name.
        relative_path: Path relative to the root (source or target).
        is_dir: Whether this node is a directory.
        in_source: Whether this node exists in the source dotfiles directory.
        in_target: Whether this node exists in the target (home) directory.
        is_symlink: Whether the target is a symlink to the source.
        has_backup: Whether a backup exists for this node.
        change: The type of change to be applied.
        children: Child nodes if this is a directory.
    """

    name: str
    relative_path: Path
    is_dir: bool = False
    in_source: bool = False
    in_target: bool = False
    is_symlink: bool = False
    has_backup: bool = False
    change: Optional[ChangeType] = None
    children: Dict[str, "ConfigNode"] = field(default_factory=dict)


class ConfigTree:
    """Represents the configuration tree for source and target directories.

    Provides methods to manage and filter configuration nodes from both
    source (dotfiles) and target (home) directories.

    Attributes:
        SOURCE: NodeOrigin enum value for source.
        TARGET: NodeOrigin enum value for target.
    """

    SOURCE = NodeOrigin.SOURCE
    TARGET = NodeOrigin.TARGET

    def __init__(self, source_path: Path, target_path: Path):
        """Initialize the ConfigTree.

        Args:
            source_path: Path to the source dotfiles directory.
            target_path: Path to the target (home) directory.
        """
        self.origins: Dict[NodeOrigin, Path] = {
            NodeOrigin.SOURCE: source_path,
            NodeOrigin.TARGET: target_path,
        }

        self._nodes: Dict[str, ConfigNode] = {}
        self.source_keys: Set[str] = set()
        self.target_keys: Set[str] = set()

    def get_tree(self) -> Dict[str, ConfigNode]:
        """Get all nodes in the tree."""
        return self._nodes

    def create_new_tree(self) -> "ConfigTree":
        """Create a new empty ConfigTree with the same origins."""
        new_tree = ConfigTree(
            self.origins[NodeOrigin.SOURCE], self.origins[NodeOrigin.TARGET]
        )
        return new_tree

    def get_relative_path(self, item: Path, origin: NodeOrigin) -> Path:
        """Get path relative to the origin root.

        Args:
            item: Absolute path to the item.
            origin: The origin (SOURCE or TARGET).

        Returns:
            Path relative to the origin root.
        """
        return item.relative_to(self.origins[origin])

    def add_node(self, node: ConfigNode, origin: NodeOrigin) -> None:
        """Add a node to the tree.

        Args:
            node: The ConfigNode to add.
            origin: The origin of the node.
        """
        self._nodes[node.name] = node
        if origin == NodeOrigin.SOURCE:
            self.source_keys.add(node.name)
        elif origin == NodeOrigin.TARGET:
            self.target_keys.add(node.name)

    def create_node(self, name: str, item: Path, origin: NodeOrigin) -> ConfigNode:
        """Create a ConfigNode from a path and origin.

        Args:
            name: The name of the node.
            item: The path to the item.
            origin: The origin of the node.

        Returns:
            A new ConfigNode instance.
        """
        return ConfigNode(
            name=name,
            relative_path=self.get_relative_path(item, origin),
            is_dir=item.is_dir(),
            in_source=(origin == NodeOrigin.SOURCE),
            in_target=(origin == NodeOrigin.TARGET),
        )

    def create_and_add_node(
        self, name: str, item: Path, origin: NodeOrigin
    ) -> ConfigNode:
        """Create and add a node to the tree.

        Args:
            name: The name of the node.
            item: The path to the item.
            origin: The origin of the node.

        Returns:
            The created ConfigNode.
        """
        node = self.create_node(name, item, origin)
        self.add_node(node, origin)
        return node

    def get_source_tree(self) -> "ConfigTree":
        """Get tree containing only nodes from source (not in target)."""
        source_only_keys = self.source_keys - self.target_keys

        return self.get_filtered_tree(source_only_keys, NodeOrigin.SOURCE)

    def get_target_tree(self) -> "ConfigTree":
        """Get tree containing only nodes from target (not in source)."""
        target_only_keys = self.target_keys - self.source_keys

        return self.get_filtered_tree(target_only_keys, NodeOrigin.TARGET)

    def get_target_hard_tree(self) -> "ConfigTree":
        """Get tree containing only symlink nodes from target."""
        target_only_keys = self.target_keys - self.source_keys
        return self.get_filtered_tree(
            target_only_keys, NodeOrigin.TARGET, lambda node: node.is_symlink is True
        )

    def get_filtered_tree(
        self, keys: Set[str], origin: NodeOrigin, filter_func=None
    ) -> "ConfigTree":
        """Get a filtered tree based on keys and optional filter function.

        Args:
            keys: Set of node names to include.
            origin: The origin for the new tree.
            filter_func: Optional filter function to apply.

        Returns:
            A new ConfigTree with filtered nodes.
        """
        new_tree = self.create_new_tree()
        for name in keys:
            node = self._nodes[name]
            if filter_func is None or filter_func(node):
                new_tree.add_node(node, origin=origin)

        return new_tree

    def get_node(self, name: str) -> Optional[ConfigNode]:
        """Get a node by name.

        Args:
            name: The name of the node.

        Returns:
            The ConfigNode if found, None otherwise.
        """
        return self._nodes.get(name)

    def get_children(self, parent_name: str) -> List[ConfigNode]:
        """Get direct children of a parent node.

        Args:
            parent_name: The name of the parent node.

        Returns:
            List of child ConfigNodes.
        """
        return [
            node
            for node in self._nodes.values()
            if node.name.startswith(f"{parent_name}/")
            and node.name.count("/") == parent_name.count("/") + 1
        ]
