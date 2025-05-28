# coding=utf-8
"""Commands for Help"""
from controller.cli.command import Command


class HelpCommand(Command):

    def __init__(self, context):
        super().__init__(context, "help")
        self.help_text = "This command displays the help about a certain command."

    def configure_parser(self, parser):
        parser.add_argument("topic", help="Specify the topic you like to hear about", default="", nargs="?")

    def execute(self, args) -> bool:
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
                self.context.print("\tmacros -- Display the available macros.")
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
            case "macro":
                self.context.print("Control macros.")  # TODO
                self.context.print("\texec <macro> -- Execute the macro")
                # TODO
            case _:
                self.context.print(f"ERROR: The requested help topic '{args.topic}' is unknown.")
                self.context.print("The following topics are known:")
                self.context.print("\tevent\tselect\tlist\tpatch\tbank_set\tshowctl\tdelay\tmacro")
                return False
        return True
