"""Module contains asset manipulation command."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from controller.cli.command import Command
from model.media_assets.asset_loading_factory import load_asset

if TYPE_CHECKING:
    from argparse import Namespace, ArgumentParser

    from controller.cli.cli_context import CLIContext

class AssetCommand(Command):
    """Command to control assets."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize AssetCommand."""
        super().__init__(context, "asset")
        self.help_text = "This command manages show file assets."

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(help="Subcommands", dest="action")
        load_parser = subparsers.add_parser("load", help="load asset", exit_on_error=False)
        load_parser.add_argument("asset-class", help="The asset class to load", type=str)
        load_parser.add_argument("info", help="The info data for that class (for example path or URI)",
                                 type=str)

    @override
    def execute(self, args: Namespace) -> bool:
        match args.action:
            case "load":
                return load_asset("", args.asset_class, args.info,
                                  self.context.show.file_path if self.context.show is not None else "") is not None
            case _:
                self.context.print("Error: Unknown asset action.")
                return False
