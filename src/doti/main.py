"""Doti - Dotfile management tool CLI entry point."""

from doti.core.engine import Doti
from doti.core.ui import TUI
from doti.core.settings import SettingsManager
import argparse
from typing import Optional


def main() -> None:
    """
    Main entry point for the Doti CLI.

    Parses command-line arguments and dispatches to the appropriate handler.
    """
    parser = argparse.ArgumentParser(
        description="Doti - Manage your dotfiles across machines."
    )

    parser.add_argument(
        "action",
        choices=["migrate", "manage"],
        help="The action to perform: 'migrate' or 'manage'",
    )

    parser.add_argument(
        "-c",
        "--config",
        required=False,
        help="Path to the configuration file",
        metavar="FILE",
    )

    parser.add_argument(
        "-s",
        "--source",
        required=False,
        help="Path to the dotfiles",
        metavar="FILE",
    )

    args = parser.parse_args()

    if args.action == "migrate":
        handle_migrate(args.config)
    elif args.action == "manage":
        handle_manage(args.config, args.source)


def migrate_to_repo() -> None:
    """Placeholder for migrating existing configs to repository."""
    pass


def handle_migrate(config_path: Optional[str]) -> None:
    """
    Handle the migrate action.

    Args:
        config_path: Optional path to configuration file.
    """
    pass


def handle_manage(config: Optional[str], source: Optional[str]) -> None:
    """
    Handle the manage action - interactive dotfile management.

    Args:
        config: Optional path to configuration file.
        source: Optional path to dotfiles source directory.
    """
    cfg = SettingsManager(config, source)
    tui = TUI(cfg)
    doti = Doti(cfg)

    source_files = doti.get_source_only()

    selection = tui.render(source_files)

    if selection is None:
        print("Selection cancelled.")
        return

    changes = doti.calculate_plan(source_files, selection)

    if cfg.confirm_changes:
        tui.print_action_plan(changes)
        if tui.confirm("Apply Changes?"):
            doti.process_plan(changes)
    else:
        doti.process_plan(changes)


if __name__ == "__main__":
    main()
