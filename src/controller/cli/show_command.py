from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from controller.cli.cli_context import CLIContext
from controller.cli.command import Command
from controller.file.read import read_document
from controller.file.transmitting_to_fish import transmit_to_fish


class ShowCommand(Command):

    def __init__(self, context: "CLIContext"):
        super().__init__(context, "showctl")

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers(help="showctl commands", dest="showaction")
        commit_parser = subparsers.add_parser("commit", help="Commit the current show file state", exit_on_error=False)
        commit_parser.add_argument("--select-default-scene", help="Load the default scene after commit",
                                   action='store_true')
        load_parser = subparsers.add_parser("load", help="Load a show file", exit_on_error=False)
        load_parser.add_argument("filename", help="The location of the .show file.")
        scene_parser = subparsers.add_parser("select-scene", help="select a specific scene in the running show.", exit_on_error=False)
        scene_parser.add_argument("scene-id", help="The scene id to select", type=int)
        filtercmd_parser = subparsers.add_parser("filtermsg", help="Send an update to a filter", exit_on_error=False)
        filtercmd_parser.add_argument("scene-id", help="The scene id to select", type=int)
        filtercmd_parser.add_argument("filter-id", help="The filter to update")
        filtercmd_parser.add_argument("parameter-key", help="The key of the parameter to update")
        filtercmd_parser.add_argument("parameter-value", help="The value to transmit")

    def execute(self, args) -> bool:
        match args.showaction:
            case "commit":
                return transmit_to_fish(self.context.show, goto_default_scene=args.select_default_scene)
            case "load":
                return read_document(args.filename, self.context.show)
            case "select-scene":
                scene = self.context.show.get_scene_by_id(args.scene_id)
                if not scene:
                    self.context.print("ERROR: scene not found.")
                    return False
                self.context.show.broadcaster.change_active_scene.emit(scene)
                return True
