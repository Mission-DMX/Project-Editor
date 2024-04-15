from controller.cli.cli_context import CLIContext
from controller.cli.command import Command
from controller.file.transmitting_to_fish import transmit_to_fish


class ShowCommand(Command):

    def __init__(self, context: CLIContext):
        super().__init__(context, "showctl")

    def configure_parser(self, parser):
        parser.add_argument("action", help="What should be done with the current show file?")

    def execute(self, args) -> bool:
        match args.action:
            case "commit":
                # TODO we should introduce a parameter to control if we'd like to switch to the default scene
                return transmit_to_fish(self.context.show)

