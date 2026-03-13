"""Terminal User Interface for Doti."""

import questionary
from prompt_toolkit.styles import Style
import sys
from typing import Dict, List, Optional, Union

from doti.utils.data import ConfigNode, ChangeType
from doti.core.settings import SettingsManager


class TUI:
    """
    Terminal User Interface for Doti interactive dotfile management.

    Provides interactive prompts for selecting, viewing, and applying
    configuration changes.
    """

    def __init__(self, settings: SettingsManager) -> None:
        """
        Initialize the TUI.

        Args:
            settings: Settings manager instance.
        """
        self.styles = self.get_styles()
        self.cfg = settings

    def get_styles(self) -> Style:
        """
        Get the prompt toolkit styles for the interface.

        Returns:
            Style object for questionary prompts.
        """
        return Style(
            [
                ("qmark", "hidden"),
                ("instruction", "fg:gray"),
                ("selected", "noreverse"),
                ("pointer", "bold"),
                ("checkbox", "fg:white"),
            ]
        )

    def clear_output(self, n: int = 1) -> None:
        """
        Clear previous lines from terminal output.

        Args:
            n: Number of lines to clear.
        """
        for _ in range(n):
            sys.stdout.write("\033[F\033[K")
        sys.stdout.flush()

    def render(self, nodes: Dict[str, ConfigNode]) -> Optional[List[ConfigNode]]:
        """
        Render the interactive selection menu for configuration nodes.

        Args:
            nodes: Dictionary of ConfigNodes to display for selection.

        Returns:
            List of selected ConfigNodes, or None if cancelled.
        """
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

    def confirm(self, message: str) -> bool:
        """
        Show a confirmation prompt.

        Args:
            message: Question to ask the user.

        Returns:
            True if user confirmed, False otherwise.
        """
        response = questionary.confirm(
            message, default=True, style=self.styles, qmark=""
        ).ask()
        self.clear_output()
        return response

    def build_choices(
        self, nodes: Dict[str, ConfigNode], prefix: str = ""
    ) -> List[Union[str, questionary.Choice]]:
        """
        Build the choices list for the checkbox prompt, including directory structure.

        Args:
            nodes: Dictionary of ConfigNodes to convert to choices.
            prefix: Prefix for indentation (used for recursion).

        Returns:
            List of questionary Choice objects and separators.
        """
        choices: List[Union[str, questionary.Choice]] = []
        items = list(nodes.items())

        for i, (name, node) in enumerate(items):
            is_last = i == len(items) - 1
            branch = "└── " if is_last else "├── "

            status_icon = f" {self.cfg.link_icon}" if node.is_symlink else ""
            backup_icon = f" {self.cfg.backup_icon}" if node.has_backup else ""
            display_name = f"{prefix}{branch}{name}{status_icon}{backup_icon}"

            if node.is_dir and node.children:
                choices.append(questionary.Separator(f"  ├── {node.name}/"))
                new_prefix = prefix + ("    " if is_last else "│   ")
                choices.extend(self.build_choices(node.children, new_prefix))

            else:
                choices.append(
                    questionary.Choice(
                        title=display_name,
                        value=node,
                        checked=node.is_symlink,
                    )
                )

        return choices

    def get_choices(
        self, nodes: Dict[str, ConfigNode]
    ) -> List[Union[str, questionary.Choice]]:
        """
        Get the full choices list with header for the target directory.

        Args:
            nodes: Dictionary of ConfigNodes.

        Returns:
            List of choices with target directory header.
        """
        choices = self.build_choices(nodes)
        choices.insert(0, questionary.Separator(f"\n  {self.cfg.target}/"))
        return choices

    def print_action_plan(self, plan: List[ConfigNode]) -> None:
        """
        Print a formatted action plan showing pending changes.

        Args:
            plan: List of ConfigNodes with change types set.
        """
        tree_map: Dict[str, List[ConfigNode]] = {}
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

        sorted_parents = sorted(tree_map.keys(), key=lambda x: (x != ".", x))

        for p_idx, parent in enumerate(sorted_parents):
            is_last_parent = p_idx == len(sorted_parents) - 1

            if parent != ".":
                char = "└──" if is_last_parent else "├──"
                print(f"{char} {parent}/")

            children = tree_map[parent]
            for c_idx, node in enumerate(children):
                is_last_child = c_idx == len(children) - 1

                action = "[+]" if node.change == ChangeType.ADD else "[-]"

                secondary = ""
                if node.change == ChangeType.ADD and node.in_target:
                    secondary = "[B]"
                elif node.change == ChangeType.REMOVE and node.has_backup:
                    secondary = "[R]"

                if parent == ".":
                    connector = "└──" if is_last_child and is_last_parent else "├──"
                    indent = ""
                else:
                    connector = "└──" if is_last_child else "├──"
                    indent = "    " if is_last_parent else "│   "

                print(f"{indent}{connector} {action} {node.name} {secondary}")
        print()
