"""Contains extract command."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from controller.cli.command import Command

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext


class ExtractCommand(Command):
    """Command to extract element from list."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize the command."""
        super().__init__(context, "extract")
        self._help_text = "Extract element from list"

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("destination", type=str, help="Destination variable.")
        parser.add_argument("element", type=int, help="Index of element to extract.")
        subparsers = parser.add_subparsers(dest="target", help="Extraction target.")
        for target in ["filter-param", "filter-config"]:
            filter_param_parser = subparsers.add_parser(
                target,
                help=f"Extract {target} from filter.",
                exit_on_error=False
            )
            filter_param_parser.add_argument("--scene", type=int, default=-1,
                                             help="Scene of the filter. Default: Current selected scene.")
            filter_param_parser.add_argument("fid", type=str, help="Filter ID.")
            filter_param_parser.add_argument("parameter", type=str, help="The parameter to extract.")
            filter_param_parser.add_argument("delimiter", type=str, help="The delimiter to use.")

    @override
    def execute(self, args: Namespace) -> bool:
        match args.target:
            case "filter-param" | "filter-config":
                scene = args.scene
                if scene == -1:
                    scene = self.context.selected_scene
                if scene is None:
                    self.context.print("Error: No scene specified.")
                    return False
                if isinstance(scene, int):
                    scene = self.context.show.get_scene_by_id(scene)
                if scene is None:
                    self.context.print("Error: No scene with specified ID exists.")
                    return False
                filter_inst = scene.get_filter_by_id(args.fid)
                if filter_inst is None:
                    self.context.print(f"Error: No filter with ID '{args.fid}' not found.")
                    return False
                selected_dict = filter_inst.initial_parameters if args.target == "filter-param"\
                    else filter_inst.filter_configurations
                splitted_param = selected_dict.get(args.parameter, "").split(args.delimiter)
                element = splitted_param[args.element] if abs(args.element) < len(splitted_param) else ""
                if len(args.destination) < 0:
                    self.context.print("Error: Invalid destination variable.")
                    return False
                self.context.update_variables({args.destination: element})
                return True
