"""Commands for selection."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from controller.cli.command import Command
from model.control_desk import BankSet

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext


def find_bank_set(identifier: str) -> BankSet | None:
    """Find a bank set by its identifier.

    Args:
        identifier: the identifier of the bank set

    Returns:
        bank set or none if the identifier not exists

    """
    linked_sets = BankSet.get_linked_bank_sets()
    try:
        return linked_sets[int(identifier)]
    except KeyError as _:
        for bank_set in linked_sets:
            if bank_set.id == identifier:
                return bank_set
    return None


class SelectCommand(Command):
    """Selected Command."""

    def __init__(self, context: CLIContext) -> None:
        """Select Command."""
        super().__init__(context, "select")
        self.help_text = "This command displays the help about a certain command."

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("what", help="Specify what you would like to select")
        parser.add_argument("item", help="Specify the item you would like to select")

    @override
    def execute(self, args: Namespace) -> bool:
        match args.what:
            case "scene":
                try:
                    scene_id = int(args.item)
                except:
                    self.context.print(f"Selected scene '{args.item}' could not get parsed as integer id.")
                    return True
                candidate = self.context.show.get_scene_by_id(scene_id)
                if candidate is None:
                    self.context.print(f"No scene with id {candidate} was found.")
                    return False
                self.context.selected_scene = candidate
                self.context.print(f"Selected scene '{candidate.human_readable_name}'.")
                return True
            case "column":
                self.context.print("ERROR: Not yet implemented.")
                return False
            case "bank_set":
                found_bank_set = find_bank_set(args.item)
                if found_bank_set:
                    self.context.selected_bank = found_bank_set
                    return True

                self.context.print(f"ERROR: the requested bank set '{args.item}' was not found")
            case _:
                self.context.print(
                    f"ERROR: The resource '{args.what}' cannot be selected. Type 'help select' to obtain a list."
                )
                return False
        return True
