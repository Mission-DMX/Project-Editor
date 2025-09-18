"""Client Commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from controller.cli.command import Command
from model.control_desk import BankSet, ColorDeskColumn
from model.media_assets.media_type import MediaType
from model.media_assets.registry import get_all_assets_of_type

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext


class ListCommand(Command):
    """Commands to list show and client state."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize ListCommand."""
        super().__init__(context, "list")
        self.help_text = "This command displays the content of system collections."

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("section", help="The section of which content should be listed")

    @override
    def execute(self, args: Namespace) -> bool:
        match args.section:
            case "scenes":
                self.context.print(" ID | Description")
                for scene in self.context.show.scenes:
                    self.context.print(f"{scene.scene_id} | {scene.human_readable_name}")
                return True
            case "filters":
                if self.context.selected_scene is None:
                    self.context.print("ERROR: No scene selected..")
                    return False
                self.context.print("Filter ID - Filter Type")
                for f in self.context.selected_scene.filters:
                    self.context.print(f"{f.filter_id} - {f.filter_type}")
                return True
            case "columns":
                if self.context.selected_bank is None:
                    self.context.print("ERROR: No bank set selected")
                    return False
                self.context.print("Type - Column description")
                for bank in self.context.selected_bank.banks:
                    self.context.print("==================================")
                    for c in bank.columns:
                        self.context.print(
                            f"{'Color' if isinstance(c, ColorDeskColumn) else 'Number'} - {c.display_name}"
                        )
                return True
            case "macros":
                for m in self.context.show.macros:
                    self.context.print(m.name)
                return True
            case "variables":
                for k, v in self.context.variables.items():
                    self.context.print(f"{k}={v}")
                return True
            case "bank_sets":
                self.context.print(" Bank Set ID                         | Description ")
                self.context.print("===================================================")
                selected_bank_set_id = self.context.selected_bank.id if self.context.selected_bank else ""
                for bs in BankSet.get_linked_bank_sets():
                    self.print_bank_set_entry(bs, selected_bank_set_id)
                if self.context.selected_bank and not self.context.selected_bank.is_linked:
                    self.print_bank_set_entry(self.context.selected_bank, selected_bank_set_id)
                return True
            case "all-assets":
                self._list_assets_by_type()
                return True
            case "image-assets":
                self._list_assets_by_type([MediaType.IMAGE])
                return True
            case "video-assets":
                self._list_assets_by_type([MediaType.VIDEO])
                return True
            case "audio-assets":
                self._list_assets_by_type([MediaType.AUDIO])
                return True
            case "3d-assets":
                self._list_assets_by_type([MediaType.MODEL_3D])
                return True
            case "text-assets":
                self._list_assets_by_type([MediaType.TEXT])
                return True
            case _:
                self.context.print(f"ERROR: The requested container '{args.section}' was not found.")
                return False

    def _list_assets_by_type(self, filter: list[MediaType] | None = None) -> None:
        """List assets based on the provided filter"""
        if filter is None:
            filter = [MediaType.IMAGE, MediaType.VIDEO, MediaType.AUDIO, MediaType.MODEL_3D, MediaType.TEXT]
        self.context.print(" Type  | UUID                                | class                      ")
        self.context.print("=======|=====================================|============================")
        for asset_type in filter:
            for asset in get_all_assets_of_type(asset_type):
                print(f" {asset.get_type().get_padded_description()} | {asset.id} |"
                      f" {str(asset.get_factory_object_hint())}")

    def print_bank_set_entry(self, bs: BankSet, selected_bank_set_id: str) -> None:
        """Print the entry of a bank set."""
        # TODO id not string
        preamble = "*" if bs.id == selected_bank_set_id else " "
        if bs.is_linked:
            self.context.print(preamble + bs.id + " | " + bs.description)
        else:
            self.context.print(preamble + "Warning: Not yet linked.         | " + bs.description)
