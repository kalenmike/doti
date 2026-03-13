from doti.utils.data import ConfigNode, ChangeType
from pathlib import Path
from typing import Dict, Set, Callable, List
import sys


class Doti:
    def __init__(self, settings):
        self.cfg = settings

        self.tree: Dict[str, ConfigNode] = {}
        self.allowed_dirs: Set[str] = set()
        self.generate_tree()

    def exists(self, target):
        return target.exists() or target.is_symlink()

    def create_backup(self, target):
        if self.exists(target):
            backup = self.get_backup_path(target)
            # print(f"Backing up {target} to {backup}")
            target.rename(backup)

    def restore_backup(self, target):
        backup = self.get_backup_path(target)
        if backup.exists():
            # print(f"Restoring backup {backup} to {target}")
            backup.rename(target)

    def has_backup(self, target):
        backup = self.get_backup_path(target)
        return backup.exists()

    def has_symlink(self, source, target):
        # Prevent bugs when passing the same filename for both parameters
        if source == target:
            raise ValueError("Source and Target cannot be the same!\n")
        return target.is_symlink() and target.resolve() == source.resolve()

    def create_symlink(self, source, target):
        self.create_backup(target)
        target.symlink_to(source)

    def remove_symlink(self, target):
        target.unlink()
        self.restore_backup(target)

    def get_backup_path(self, p):
        """Inserts .bkp before the extension or at the end of the folder name."""
        if p.is_dir():
            return p.with_name(f"{p.name}{self.cfg.backup_suffix}")

        # Handle files: insert .bkp before the suffix
        # e.g., .test.sh -> .test.bkp.sh
        # Note: .test has an empty suffix in pathlib, so we handle it as a suffix
        parts = p.name.split(".")
        if len(parts) <= 2:  # Simple case like .test or test.sh
            return p.with_name(f"{p.name}{self.cfg.backup_suffix}")

        # Complex case: insert before the final extension
        return p.with_name(f"{p.stem}{self.cfg.backup_suffix}{p.suffix}")

    def move_config_to_source(self):
        # move
        # create symlink
        pass

    def find_new_configs(self):
        # Find configs in home that are not in source
        pass

    def get_label(self, item, exists=False, backup=False):
        state = f" {self.cfg.link_icon}" if exists else ""
        backup = f" {self.cfg.backup_icon}" if backup else ""
        return f"{item}{state}{backup}"

    def generate_tree(self):
        if not self.cfg.source.exists():
            print("Your source is not configured. Pass a config file to continue.")
            sys.exit()
        elif not self.cfg.target.exists():
            print("Your home does not exist. Check your config file.")
            sys.exit()

        self.scan_source()
        self.scan_target()

    def print_tree(self, tree):
        """Prints a visual representation of the config tree."""
        # Print header
        print(f"{'Name':<20} | {'Source':<8} | {'Target':<8} | {'Is Dir':<8}")
        print("-" * 55)

        def walk(nodes: Dict[str, ConfigNode], indent: str = ""):
            for name, node in nodes.items():
                # Format boolean values for readability
                src = "Yes" if node.in_source else "No"
                tgt = "Yes" if node.in_target else "No"
                d = "Yes" if node.is_dir else "No"

                print(
                    f"{indent}{name:<{20 - len(indent)}} | {src:<8} | {tgt:<8} | {d:<8}"
                )

                # Recurse only if it's a directory
                if node.is_dir and node.children:
                    walk(node.children, indent + "  ")

        walk(tree)

    def filter_tree(
        self, predicate: Callable[[ConfigNode], bool]
    ) -> Dict[str, ConfigNode]:
        """
        Returns a new dictionary containing only nodes that satisfy the predicate.
        """

        def walk(nodes: Dict[str, ConfigNode]) -> Dict[str, ConfigNode]:
            filtered = {}
            for name, node in nodes.items():
                # Check the current node against the predicate
                if predicate(node):
                    # Create a new instance (shallow copy) to keep the original tree intact
                    new_node = ConfigNode(
                        name=node.name,
                        relative_path=node.relative_path,
                        is_dir=node.is_dir,
                        in_source=node.in_source,
                        in_target=node.in_target,
                        is_symlink=node.is_symlink,
                        has_backup=node.has_backup,
                        children=walk(node.children),  # Recursively filter children
                    )
                    filtered[name] = new_node
                # If the node doesn't match, we essentially 'prune' it from the result
            return filtered

        return walk(self.tree)

    def get_source_only(self) -> Dict[str, ConfigNode]:
        # Include if it exists in the source
        return self.filter_tree(lambda node: node.in_source)

    def get_target_only(self) -> Dict[str, ConfigNode]:
        # Include if it exists in the target but NOT the source
        return self.filter_tree(lambda node: node.in_target and not node.is_symlink)

    def scan_source(self):
        # Scan root level (depth 0)
        for item in self.cfg.source.iterdir():
            prefix = self.get_dot_prefix(item.name)
            name = f"{prefix}{item.name}"
            node = ConfigNode(
                name=name,
                relative_path=item.relative_to(self.cfg.source),
                is_dir=item.is_dir(),
                in_source=True,
            )
            self.tree[name] = node

            # If it's a directory, scan its children (depth 1), but don't go deeper
            if node.is_dir:
                self.allowed_dirs.add(name)  # Register as allowed
                for sub_item in item.iterdir():
                    child = ConfigNode(
                        name=sub_item.name,
                        relative_path=sub_item.relative_to(self.cfg.source),
                        is_dir=sub_item.is_dir(),
                        in_source=True,
                    )
                    node.children[sub_item.name] = child

    def scan_target(self):
        # 1. Scan root files/dirs
        for item in self.cfg.target.iterdir():
            # Only process if hidden or in our pre-scanned allowed paths
            if not (item.name.startswith(".") or item.name in self.allowed_dirs):
                continue

            node = self.tree.get(item.name)
            if not node:
                # Only exists in target
                node = ConfigNode(
                    name=item.name,
                    relative_path=item.relative_to(self.cfg.target),
                    is_dir=item.is_dir(),
                )
                self.tree[item.name] = node

            else:
                # Exists in source
                has_symlink = self.has_symlink(
                    self.cfg.source / node.relative_path, item
                )
                node.is_symlink = has_symlink
                if has_symlink:
                    node.has_backup = self.has_backup(item)

            node.in_target = True

            # 2. If it's a directory, scan just one level deeper
            if node.is_dir and item.name in self.allowed_dirs:
                for sub_item in item.iterdir():
                    child = node.children.get(sub_item.name)
                    if not child:
                        child = ConfigNode(
                            name=sub_item.name,
                            relative_path=sub_item.relative_to(self.cfg.target),
                            is_dir=sub_item.is_dir(),
                        )
                        node.children[sub_item.name] = child
                    else:
                        has_symlink = self.has_symlink(
                            self.cfg.source / child.relative_path, sub_item
                        )
                        child.is_symlink = has_symlink
                        if has_symlink:
                            child.has_backup = self.has_backup(sub_item)

                    child.in_target = True

    def flatten_tree(self, nodes: Dict[str, ConfigNode]) -> List[ConfigNode]:
        """
        Recursively flattens the ConfigNode tree into a single list.
        """
        flat_list = []
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
        # 1. Convert selected to a set of paths for O(1) lookups
        selected_paths = {node.relative_path for node in selected_nodes}

        available_nodes = self.flatten_tree(all_available_nodes)

        plan = []

        for node in available_nodes:
            is_currently_active = node.is_symlink  # Or whatever defines "installed"
            is_now_selected = node.relative_path in selected_paths

            if is_now_selected and not is_currently_active:
                # Action: Create Symlink
                node.change = ChangeType.ADD
                plan.append(node)
            elif not is_now_selected and is_currently_active:
                # Action: Remove Symlink
                node.change = ChangeType.REMOVE
                plan.append(node)

        return plan

    def process_plan(self, nodes):
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
        s = name.as_posix() if isinstance(name, Path) else name
        return "." if self.cfg.add_dot and not s.startswith(".") else ""

    def migrate(self):
        pass
