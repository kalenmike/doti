"""Data structures for Doti configuration management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
from enum import Enum


class ChangeType(Enum):
    """Represents the type of change to be applied to a configuration node."""

    ADD = "ADD"
    REMOVE = "REMOVE"
    KEEP = "KEEP"


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
