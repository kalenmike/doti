import questionary
from prompt_toolkit.styles import Style
import sys
from typing import Dict, List, Union

from doti.utils.data import ConfigNode, ChangeType


class TUI:
    def __init__(self, settings):
        self.styles = self.get_styles()
        self.cfg = settings

    def get_styles(self):
        return Style(
            [
                ("qmark", "hidden"),
                ("instruction", "fg:gray"),
                ("selected", "noreverse"),
                ("pointer", "bold"),  # Keeps the pointer visible
                ("checkbox", "fg:white"),  # Customizes checkbox color
            ]
        )

    def clear_output(self, n=1):
        for _ in range(n):
            sys.stdout.write("\033[F\033[K")
        sys.stdout.flush()

    def render(self, nodes):
        try:
            choices = self.get_choices(nodes)
            enter_msg = (
                "to preview changes" if self.cfg.confirm_changes else "to apply changes"
            )

            selection = questionary.checkbox(
                "Install your dotfiles:",
                qmark="",
                instruction=f"\n ● Install | ○ Remove | Installed {self.cfg.link_icon} | Backup {self.cfg.backup_icon}\n <Space> to toggle, <Enter> {enter_msg}",
                choices=choices,
                style=self.styles,
            ).unsafe_ask()

            self.clear_output(1)

            return selection
        except KeyboardInterrupt:
            self.clear_output(3)
            print("Exiting...")
            sys.exit(0)

    def confirm(self, message):
        response = questionary.confirm(
            message, default=True, style=self.styles, qmark=""
        ).ask()
        self.clear_output()
        return response

    def build_choices(
        self, nodes: Dict[str, ConfigNode], prefix: str = ""
    ) -> List[Union[str, questionary.Choice]]:

        choices = []
        items = list(nodes.items())

        for i, (name, node) in enumerate(items):
            is_last = i == len(items) - 1
            branch = "└── " if is_last else "├── "

            # Determine the visual status indicator
            status_icon = f" {self.cfg.link_icon}" if node.is_symlink else ""
            backup_icon = f" {self.cfg.backup_icon}" if node.has_backup else ""
            display_name = f"{prefix}{branch}{name}{status_icon}{backup_icon}"

            # If directory, recurse into children (level 2)
            if node.is_dir and node.children:
                choices.append(questionary.Separator(f"  ├── {node.name}/"))
                new_prefix = prefix + ("    " if is_last else "│   ")
                choices.extend(self.build_choices(node.children, new_prefix))

            else:
                # Add the node as a Choice object
                choices.append(
                    questionary.Choice(
                        title=display_name,
                        value=node,  # We store the node object itself for easy processing later
                        checked=node.is_symlink,
                    )
                )

        return choices

    def get_choices(self, nodes) -> List[Union[str, questionary.Choice]]:
        choices = self.build_choices(nodes)
        choices.insert(0, questionary.Separator(f"\n  {self.cfg.target}/"))
        return choices

    def print_action_plan_(self, plan: List[ConfigNode]):
        # 1. Group items by their parent directory
        # Using a dict to map parent -> list of children
        tree_map = {}
        print("Pending Changes:")
        print(f"\n{self.cfg.target}/")
        for node in plan:
            parent = str(node.relative_path.parent)
            if parent not in tree_map:
                tree_map[parent] = []
            tree_map[parent].append(node)

        # 2. Print root items first, then children
        # We sort keys so parents come first
        for parent in sorted(tree_map.keys()):
            # If parent is not root, print it as a header
            if parent != ".":
                print(f"├── .{parent}/")

            # Print children under the parent
            for node in tree_map[parent]:
                # Assemble Action & Backup indicators
                action = "[+]" if node.change == ChangeType.ADD else "[-]"
                secondary = (
                    "[B]"
                    if (node.change == ChangeType.ADD and node.in_target)
                    else "   "
                )

                # Indent if inside a folder
                indent = "│   " if parent != "." else ""
                print(f"{indent}├── {action:<4} {node.name} {secondary:<4} ")
        print()

    def print_action_plan(self, plan: List[ConfigNode]):
        # 1. Group items by their parent directory
        tree_map = {}
        for node in plan:
            parent = str(node.relative_path.parent)
            if parent not in tree_map:
                tree_map[parent] = []
            tree_map[parent].append(node)

        questionary.print("Pending Changes:", style="bold")
        questionary.print(
            "[+] Install | [-] Remove | Backup [B] | Restore [R]", style="fg:gray"
        )
        questionary.print(f"\n{self.cfg.target}/")

        # Sort parents so root (.) comes first, then alphabetically
        sorted_parents = sorted(tree_map.keys(), key=lambda x: (x != ".", x))

        for p_idx, parent in enumerate(sorted_parents):
            is_last_parent = p_idx == len(sorted_parents) - 1

            # Determine the header for the directory
            if parent != ".":
                char = "└──" if is_last_parent else "├──"
                print(f"{char} {parent}/")

            # Process children within this directory
            children = tree_map[parent]
            for c_idx, node in enumerate(children):
                is_last_child = c_idx == len(children) - 1

                # Action and Backup icons
                action = "[+]" if node.change == ChangeType.ADD else "[-]"

                secondary = ""
                if node.change == ChangeType.ADD and node.in_target:
                    secondary = "[B]"
                elif node.change == ChangeType.REMOVE and node.has_backup:
                    secondary = "[R]"

                # Logic for connectors
                if parent == ".":
                    # Root level items
                    connector = "└──" if is_last_child and is_last_parent else "├──"
                    indent = ""
                else:
                    # Nested items
                    connector = "└──" if is_last_child else "├──"
                    # If this isn't the last parent directory, keep the vertical pipe going
                    indent = "    " if is_last_parent else "│   "

                print(f"{indent}{connector} {action} {node.name} {secondary}")
        print()
