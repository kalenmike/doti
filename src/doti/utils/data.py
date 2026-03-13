from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
from enum import Enum


class ChangeType(Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    KEEP = "KEEP"


@dataclass
class ConfigNode:
    name: str
    relative_path: Path  # Path from root
    is_dir: bool = False  # Is a directory
    in_source: bool = False  # Exists in source
    in_target: bool = False  # Exists in target, could be symlink or unique
    is_symlink: bool = False  # Target is a symlink, no need to backup
    has_backup: bool = False  # If symlink and backup exists
    change: Optional[ChangeType] = None
    children: Dict[str, "ConfigNode"] = field(default_factory=dict)
