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
    # TODO(zen): Add docstring
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
    # TODO(zen): Add doctrings and check typehints to all methods and class
    SOURCE = NodeOrigin.SOURCE
    TARGET = NodeOrigin.TARGET

    def __init__(self, source_path: Path, target_path: Path):
        self.origins: Dict[NodeOrigin, Path] = {
            NodeOrigin.SOURCE: source_path,
            NodeOrigin.TARGET: target_path,
        }

        self._nodes: Dict[str, ConfigNode] = {}
        self.source_keys: Set[str] = set()
        self.target_keys: Set[str] = set()

    def get_tree(self) -> Dict[str, ConfigNode]:
        return self._nodes

    def create_new_tree(self) -> "ConfigTree":
        new_tree = ConfigTree(
            self.origins[NodeOrigin.SOURCE], self.origins[NodeOrigin.TARGET]
        )
        return new_tree

    def get_relative_path(self, item: Path, origin: NodeOrigin):
        return item.relative_to(self.origins[origin])

    def add_node(self, node: ConfigNode, origin: NodeOrigin) -> None:
        self._nodes[node.name] = node
        if origin == NodeOrigin.SOURCE:
            self.source_keys.add(node.name)
        elif origin == NodeOrigin.TARGET:
            self.target_keys.add(node.name)

    def create_node(self, name, item, origin: NodeOrigin):
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
        node = self.create_node(name, item, origin)
        self.add_node(node, origin)
        return node

    def get_source_tree(self) -> "ConfigTree":
        source_only_keys = self.source_keys - self.target_keys

        return self.get_filtered_tree(source_only_keys, NodeOrigin.SOURCE)

    def get_target_tree(self) -> "ConfigTree":
        target_only_keys = self.target_keys - self.source_keys

        return self.get_filtered_tree(target_only_keys, NodeOrigin.TARGET)

    def get_target_hard_tree(self) -> "ConfigTree":
        target_only_keys = self.target_keys - self.source_keys
        return self.get_filtered_tree(
            target_only_keys, NodeOrigin.TARGET, lambda node: node.is_symlink is True
        )

    def get_filtered_tree(
        self, keys: Set[str], origin: NodeOrigin, filter_func=None
    ) -> "ConfigTree":
        new_tree = self.create_new_tree()
        for name in keys:
            node = self._nodes[name]
            if filter_func is None or filter_func(node):
                new_tree.add_node(node, origin=origin)

        return new_tree

    def get_node(self, name: str) -> Optional[ConfigNode]:
        return self._nodes.get(name)

    def get_children(self, parent_name: str) -> List[ConfigNode]:
        return [
            node
            for node in self._nodes.values()
            if node.name.startswith(f"{parent_name}/")
            and node.name.count("/") == parent_name.count("/") + 1
        ]
