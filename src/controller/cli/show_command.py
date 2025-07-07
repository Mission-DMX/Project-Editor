
"""
This file contains a command implementation to control show files, including their running state on fish.
:author: Doralitze
"""

from typing import TYPE_CHECKING

from controller.cli.command import Command
from controller.file.read import read_document
from controller.file.transmitting_to_fish import transmit_to_fish

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from controller.cli.cli_context import CLIContext


class ShowCommand(Command):
    """
    Control the loadding, saving and transmitting of a show file. Furthermore, this command selection enables the
    control over a running show on fish.
    """

    def __init__(self, context: "CLIContext"):
        super().__init__(context, "showctl")

    def configure_parser(self, parser):
        """
        Configure the sub parser of the CLI.

        :param parser: The argparse subparser to configure.
        """
        subparsers = parser.add_subparsers(help="showctl commands", dest="showaction")
        commit_parser: "ArgumentParser" = subparsers.add_parser("commit", help="Commit the current show file state",
                                                                exit_on_error=False)
        commit_parser.add_argument("--select-default-scene", help="Load the default scene after commit",
                                   action='store_true')
        load_parser: "ArgumentParser" = subparsers.add_parser("load", help="Load a show file", exit_on_error=False)
        load_parser.add_argument("filename", help="The location of the .show file.")
        scene_parser: "ArgumentParser" = subparsers.add_parser("select-scene",
                                                               help="select a specific scene in the running show.",
                                                               exit_on_error=False)
        scene_parser.add_argument("sceneid", help="The scene id to select", type=int)
        filtercmd_parser: "ArgumentParser" = subparsers.add_parser("filtermsg", help="Send an update to a filter",
                                                                   exit_on_error=False)
        filtercmd_parser.add_argument("sceneid", help="The scene id to select", type=int)
        filtercmd_parser.add_argument("filterid", help="The filter to update")
        filtercmd_parser.add_argument("parameterkey", help="The key of the parameter to update")
        filtercmd_parser.add_argument("parametervalue", help="The value to transmit")

    def execute(self, args) -> bool:
        match args.showaction:
            case "commit":
                return transmit_to_fish(self.context.show, goto_default_scene=args.select_default_scene)
            case "load":
                return read_document(args.filename, self.context.show)
            case "select-scene":
                scene = self.context.show.get_scene_by_id(args.sceneid)
                if not scene:
                    self.context.print("ERROR: scene not found.")
                    return False
                self.context.networkmgr.enter_scene(scene, push_direct=False)
                return True
            case "filtermsg":
                self.context.networkmgr.send_gui_update_to_fish(args.sceneid, args.filterid,
                                                                args.parameterkey, args.parametervalue,
                                                                enque=True)
                return True
        return False
