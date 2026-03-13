from doti.core.engine import Doti
from doti.core.ui import TUI
from doti.core.settings import SettingsManager
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Doti - Manage your dotfiles across machines."
    )

    # 1. Define the positional command (migrate or manage)
    parser.add_argument(
        "action",
        choices=["migrate", "manage"],
        help="The action to perform: 'migrate' or 'manage'",
    )

    # 2. Define the config flag
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

    # Parse the arguments
    args = parser.parse_args()

    # Dispatch to the appropriate function
    if args.action == "migrate":
        handle_migrate(args.config)
    elif args.action == "manage":
        handle_manage(args.config, args.source)


def migrate_to_repo():
    pass


def handle_migrate(config_path):
    pass


def handle_manage(config, source):
    cfg = SettingsManager(config, source)
    tui = TUI(cfg)
    doti = Doti(cfg)

    # Get the files/directories in source
    source_files = doti.get_source_only()

    # Show them to the user for selection
    selection = tui.render(source_files)

    if selection is None:
        print("Selection cancelled.")
        return

    # Determine changes from users selection
    changes = doti.calculate_plan(source_files, selection)

    # doti.set_change_queue(selection)

    if cfg.confirm_changes:
        tui.print_action_plan(changes)
        # doti.preview_queue()
        if tui.confirm("Apply Changes?"):
            # doti.process_queue()
            doti.process_plan(changes)
    else:
        doti.process_plan(changes)
        # doti.process_queue()


if __name__ == "__main__":
    main()
