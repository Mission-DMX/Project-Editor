from __future__ import annotations

from typing import TYPE_CHECKING, override

from controller.cli.command import Command
from view.show_mode.player.external_ui_windows import change_window_page_index

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext

class UIPageCommand(Command):
    """Command to control UI pages and their display."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize the command."""
        super().__init__(context, "uipage")

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(help="subcommands", dest="pageaction")
        set_displayed_index = subparsers.add_parser(
            "set-displayed-index", help="Set the displayed index of extra windows.", exit_on_error=False
        )
        set_displayed_index.add_argument(
            "window", type=int, help="Specify the window whose preference you'd like to edit."
        )
        set_displayed_index.add_argument(
            "scene", type=int, help="Specify the scene for which a different page should be displayed."
        )
        set_displayed_index.add_argument(
            "index", type=int, help="Specify the page index you would like to display now."
        )

    @override
    def execute(self, args: Namespace) -> bool:
        match args.pageaction:
            case "set-displayed-index":
                window_index = args.window
                scene_index = args.scene
                displayed_index = args.index
                try:
                    change_window_page_index(window_index, scene_index, displayed_index)
                    return True
                except IndexError:
                    self.context.print("Unable to set requested UI page index. The parameters are out of range.")
                    return False
                except ValueError:
                    self.context.print("Unable to set requested UI page index. The scene parameter is out of range.")
                    return False
            case _:
                self.context.print("Unknown action requested.")
                return False
        return False
