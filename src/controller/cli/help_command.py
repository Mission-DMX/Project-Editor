"""Commands for Help."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

from controller.cli.command import Command

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext


class HelpCommand(Command):
    """Commands for Help."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize the command."""
        super().__init__(context, "help")
        self.help_text = "This command displays the help about a certain command."

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("topic", help="Specify the topic you like to hear about", default="", nargs="?")

    @override
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
                self.context.print("\tconnect -- Connect filter channels")
                self.context.print("\tscenes -- Display the available scene ids.")
                self.context.print("\tfilters -- Display the filter ids in the current selected scene.")
                self.context.print("\tcolumns -- Display the columns in the current selected bank set.")
                self.context.print("\tbank_sets -- Display the available bank sets.")
                self.context.print("\tmacros -- Display the available macros.")
                self.context.print("\tvariables -- Display all current variables.")
                self.context.print("\t<all|image|video|audio|3d|text>-assets -- Display all assets of type.")
            case "print":
                self.context.print("Print all appended arguments")
            case "set":
                self.context.print("Set the specified variable to the specified value")
            case "if":
                self.context.print("Usage: if <expression> <command>")
                self.context.print("Executes the specified command if the expression evaluates to true.")
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
                self.context.print("\tload <show file> -- Load the provided show file and make it the current one")
                self.context.print("\tfiltermsg <scene id> <filter id> <key> <value> -- Update the parameter <key> of "
                                   "\n\t\tfilter <filter id> from scene <scene id> to value <value>.")
                self.context.print("select-scene <scene id> -- switch to scene with ID <scene id>")
                self.context.print("commit [--select-default-scene] -- apply the current loaded show file to fish")
            case "delay":
                self.context.print("delay the execution of the macro by the specified amount of milliseconds")
            case "fish":
                self.context.print("Manage fish connection state.")
                self.context.print("\tconnect -- Connect to the fish")
                self.context.print("\tdisconnect -- Disconnect from the fish")
                self.context.print("\tquery -- Query the fish connection state")
            case "macro":
                self.context.print("Control macros.")  # TODO
                self.context.print("\texec <macro> -- Execute the macro")
                # TODO
            case "asset":
                self.context.print("Manipulate loaded assets.")
                self.context.print("load <class> <info>")
            case "connect":
                self.context.print("Connect filter channels. Requires to have a scene selected.")
                self.context.print("\t<source channel ID template> <destination channel ID templates> [--guard <smod:X>"
                                   "|<dmod:X>|<dt:DT>|<sfid_contains:STR>|<dfid_contains:STR>|<schan_contains:STR>|"
                                   "<dchan_contains:STR>] [--source-count <count>] [--destination-count <count>]")
            case _:
                self.context.print(f"ERROR: The requested help topic '{args.topic}' is unknown.")
                self.context.print("The following topics are known:")
                self.context.print("\tevent\tselect\tlist\tpatch\tbank_set\tshowctl\tdelay\tmacro")
                self.context.print("\tprint\tasset\tset\tif\tconnect\tfish")
                return False
        return True
