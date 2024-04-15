from controller.cli.cli_context import CLIContext
from controller.cli.command import Command
from controller.file.read import read_document
from controller.file.transmitting_to_fish import transmit_to_fish


class ShowCommand(Command):

    def __init__(self, context: CLIContext):
        super().__init__(context, "showctl")

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers(help="showctrl commands", dest="showaction")
        commit_parser = subparsers.add_parser("commit", help="Commit the current show file state")
        commit_parser.add_argument("--select-default-scene", help="Load the default scene after commit",
                                   action='store_true')
        load_parser = subparsers.add_parser("load")
        load_parser.add_argument("filename")

    def execute(self, args) -> bool:
        match args.showaction:
            case "commit":
                return transmit_to_fish(self.context.show, goto_default_scene=args.select_default_scene)
            case "load":
                return read_document(args.filename, self.context.show)

