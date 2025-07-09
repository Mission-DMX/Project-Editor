"""Commands for Help"""
from __future__ import annotations

from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from controller.cli.command import Command

if TYPE_CHECKING:
    from controller.cli.cli_context import CLIContext


class HelpCommand(Command):
    """Commands for Help"""

    def __init__(self, context: CLIContext) -> None:
        super().__init__(context, "help")
        self.help_text = "This command displays the help about a certain command."

    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("topic", help="Specify the topic you like to hear about", default="", nargs="?")

    def execute(self, args: Namespace) -> bool:
        match args.topic:
            case "select":
                self.context.print("Use this command to alter the selected regions within this context.")
                self.context.print("The following defaults can be changed:")
                self.context.print("\tscene -- Select the scene to perform actions on")
                self.context.print("\tcolumn -- Select the control desk column to perform actions on")
                self.context.print("\tbank_set -- Select the control desk bank set to perform actions on")
            case "list":
                self.context.print("This command displays the content of system collections.")
                self.context.print("The following containers can be queried:")
                self.context.print("\tscenes -- Display the available scene ids.")
                self.context.print("\tfilters -- Display the filter ids in the current selected scene.")
                self.context.print("\tcolumns -- Display the columns in the current selected bank set.")
                self.context.print("\tbank_sets -- Display the available bank sets.")
            case "patch":
                self.context.print("Patch a fixture. Usage: patch <fixture name> [number of fixtures]@<universe>"
                                   "[@<start channel>[@<offset>]]")
                self.context.print("\tfixture name -- The name of the fixture to patch")
                self.context.print("\tuniverse -- The index (not the name) of the destination universe")
                self.context.print("\tstart channel -- The start channel of the first fixture")
                self.context.print("\toffset -- The number of gap channels between fixtures (excluding the"
                                   "own length of the fixture)")
            case "bank_set":
                self.context.print("Modify the selected bank set. Usage: bank_set commit/create <description>"
                                   "/add --bank <bank> --col-type <type>/info/activate")
            case "event":
                self.context.print("Manage the fish event system")
                self.context.print("\tadd-sender -- Add a bew event sender to fish")
                self.context.print("\tsend -- Insert a new event into fish")
            case "showctl":
                self.context.print("Manage the general show file and execution on fish")
            case _:
                self.context.print(f"ERROR: The requested help topic '{args.topic}' is unknown.")
                self.context.print("The following topics are known:")
                self.context.print("\tevent\tselect\tlist\tpatch\tbank_set\tshowctl")
                return False
        return True
