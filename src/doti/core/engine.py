"""Core engine for Doti dotfile management."""

from doti.utils.data import ConfigNode, ChangeType, ConfigTree
from doti.core.settings import SettingsManager
from pathlib import Path
from typing import Dict, List, Set


class Doti:
    """
    Core engine for managing dotfile symlinks between source and target directories.

    This class handles scanning, creating backups, symlinking, and restoring
    configuration files between a dotfiles repository and the home directory.

    Attributes:
        cfg: Settings manager instance.
        tree: ConfigTree representing the configuration file tree.
        allowed_dirs: Set of directory names allowed for recursive scanning.
    """

    def __init__(self, settings: SettingsManager) -> None:
        """
        Initialize the Doti engine.

        Args:
            settings: Settings manager instance.
        """
        self.cfg = settings

        self.tree = ConfigTree(self.cfg.source, self.cfg.target)
        self.allowed_dirs: Set[str] = set()
        self.generate_tree()

    def exists(self, target: Path) -> bool:
        """
        Check if a target path exists (file, directory, or symlink).

        Args:
            target: Path to check.

        Returns:
            True if target exists, False otherwise.
        """
        return target.exists() or target.is_symlink()

    def create_backup(self, target: Path) -> None:
        """
        Create a backup of an existing file or directory.

        Args:
            target: Path to the file/directory to back up.
        """
        if self.exists(target):
            backup = self.get_backup_path(target)
            target.rename(backup)

    def restore_backup(self, target: Path) -> None:
        """
        Restore a file from its backup.

        Args:
            target: Path to restore the backup to.
        """
        backup = self.get_backup_path(target)
        if backup.exists():
            backup.rename(target)

    def has_backup(self, target: Path) -> bool:
        """
        Check if a backup exists for a target path.

        Args:
            target: Path to check for backup.

        Returns:
            True if backup exists, False otherwise.
        """
        backup = self.get_backup_path(target)
        return backup.exists()

    def has_symlink(self, source: Path, target: Path) -> bool:
        """
        Check if target is a symlink pointing to source.

        Args:
            source: Expected source path.
            target: Target path to check.

        Returns:
            True if target is a symlink to source.

        Raises:
            ValueError: If source and target are the same path.
        """
        if source == target:
            raise ValueError("Source and Target cannot be the same!\n")
        return target.is_symlink() and target.resolve() == source.resolve()

    def create_symlink(self, source: Path, target: Path) -> None:
        """
        Create a symlink from target to source, backing up target first if it exists.

        Args:
            source: Source path (in dotfiles repository).
            target: Target path (in home directory).
        """
        target.parent.mkdir(parents=True, exist_ok=True)

        self.create_backup(target)
        target.symlink_to(source)

    def remove_symlink(self, target: Path) -> None:
        """
        Remove a symlink and restore from backup if available.

        Args:
            target: Path to the symlink to remove.
        """
        target.unlink()
        self.restore_backup(target)

    def get_backup_path(self, p: Path) -> Path:
        """
        Generate the backup path for a given file or directory.

        Inserts the backup suffix before the extension or at the end of the name.

        Args:
            p: Original path.

        Returns:
            Path for the backup file.
        """
        if p.is_dir():
            return p.with_name(f"{p.name}{self.cfg.backup_suffix}")

        parts = p.name.split(".")
        if len(parts) <= 2:
            return p.with_name(f"{p.name}{self.cfg.backup_suffix}")

        return p.with_name(f"{p.stem}{self.cfg.backup_suffix}{p.suffix}")

    def move_config_to_source(self) -> None:
        """Move a configuration from target to source and create symlink."""
        pass

    def find_new_configs(self) -> None:
        """Find configurations in home that are not in source."""
        pass

    def get_label(
        self, item: str, exists: bool = False, has_backup: bool = False
    ) -> str:
        """
        Generate a display label for a configuration item.

        Args:
            item: Name of the item.
            exists: Whether the item is currently linked.
            has_backup: Whether a backup exists.

        Returns:
            Formatted label string.
        """
        state = f" {self.cfg.link_icon}" if exists else ""
        backup_str = f" {self.cfg.backup_icon}" if has_backup else ""
        return f"{item}{state}{backup_str}"

    def generate_tree(self) -> None:
        """
        Generate the configuration tree by scanning source and target directories.

        Exits if source or target directories do not exist.
        """
        if not self.cfg.source.exists():
            print("Your source is not configured. Pass a config file to continue.")
            import sys

            sys.exit()
        elif not self.cfg.target.exists():
            print("Your home does not exist. Check your config file.")
            import sys

            sys.exit()

        self.scan_source()
        self.scan_target()

    def get_source_tree(self) -> ConfigTree:
        """Get the source-only configuration tree (files only in source)."""
        return self.tree.get_source_tree()

    def get_target_tree(self) -> ConfigTree:
        """Get the target-only configuration tree (files only in target)."""
        return self.tree.get_target_tree()

    def scan_source(self) -> None:
        """
        Scan the source directory and populate the configuration tree.

        Only scans root level and one level of subdirectories.
        """
        for item in self.cfg.source.iterdir():
            prefix = self.get_dot_prefix(item.name)
            name = f"{prefix}{item.name}"

            node = self.tree.create_and_add_node(name, item, ConfigTree.SOURCE)

            if node.is_dir:
                self.allowed_dirs.add(name)
                for sub_item in item.iterdir():
                    self.tree.create_and_add_node(
                        f"{name}/{sub_item.name}", sub_item, ConfigTree.SOURCE
                    )

    def scan_target(self) -> None:
        """
        Scan the target (home) directory and update the configuration tree.

        Identifies symlinks and backups, and detects files only in target.
        """
        for item in self.cfg.target.iterdir():
            if not item.name.startswith(".") and item.name not in self.allowed_dirs:
                continue

            node = self.tree.get_node(item.name)
            if not node:
                node = self.tree.create_and_add_node(item.name, item, ConfigTree.TARGET)

            else:
                has_symlink = self.has_symlink(
                    self.cfg.source / node.relative_path, item
                )
                node.is_symlink = has_symlink
                if has_symlink:
                    node.has_backup = self.has_backup(item)
                node.in_target = True

            if node.is_dir and item.name in self.allowed_dirs:
                for sub_item in item.iterdir():
                    child = self.tree.get_node(f"{item.name}/{sub_item.name}")
                    if not child:
                        self.tree.create_and_add_node(
                            f"{item.name}/{sub_item.name}",
                            sub_item,
                            ConfigTree.TARGET,
                        )
                    else:
                        child.in_target = True
                        has_symlink = self.has_symlink(
                            self.cfg.source / child.relative_path, sub_item
                        )
                        child.is_symlink = has_symlink
                        if has_symlink:
                            child.has_backup = self.has_backup(sub_item)

    def flatten_tree(self, nodes: Dict[str, ConfigNode]) -> List[ConfigNode]:
        """
        Recursively flatten a ConfigNode tree into a list.

        Args:
            nodes: Dictionary of ConfigNodes to flatten.

        Returns:
            Flat list of all ConfigNodes.
        """
        flat_list: List[ConfigNode] = []
        for node in nodes.values():
            flat_list.append(node)
            if node.children:
                flat_list.extend(self.flatten_tree(node.children))
        return flat_list

    def calculate_plan(
        self,
        all_available_nodes: Dict[str, ConfigNode],
        selected_nodes: List[ConfigNode],
    ) -> List[ConfigNode]:
        """
        Calculate the changes needed based on selected nodes.

        Compares current state (symlinks) with desired state (selections)
        to determine what actions to take.

        Args:
            all_available_nodes: All nodes available in source.
            selected_nodes: Nodes selected by user.

        Returns:
            List of nodes with change type set.
        """
        selected_paths = {node.relative_path for node in selected_nodes}

        available_nodes = self.flatten_tree(all_available_nodes)

        plan: List[ConfigNode] = []

        for node in available_nodes:
            is_currently_active = node.is_symlink
            is_now_selected = node.relative_path in selected_paths

            if is_now_selected != is_currently_active:
                node.change = ChangeType.ADD if is_now_selected else ChangeType.REMOVE
                plan.append(node)

        return plan

    def process_plan(self, nodes: List[ConfigNode]) -> None:
        """
        Execute the planned changes (add/remove symlinks).

        Args:
            nodes: List of nodes with change type set to apply.
        """
        for node in nodes:
            prefix = self.get_dot_prefix(node.relative_path)
            src = self.cfg.source / node.relative_path
            dst = self.cfg.target / Path(f"{prefix}{node.relative_path}")

            if node.change == ChangeType.ADD:
                if node.in_target:
                    self.create_backup(dst)
                self.create_symlink(src, dst)
            elif node.change == ChangeType.REMOVE:
                self.remove_symlink(dst)
                if node.has_backup:
                    self.restore_backup(dst)

    def get_dot_prefix(self, name: str | Path) -> str:
        """
        Determine if a dot prefix should be added to a filename.

        Args:
            name: The filename or Path.

        Returns:
            "." if dot should be added, "" otherwise.
        """
        s = name.as_posix() if isinstance(name, Path) else name
        return "." if self.cfg.add_dot and not s.startswith(".") else ""

    def migrate(self) -> None:
        """Migrate existing configurations to source repository."""
        pass
