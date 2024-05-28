# coding=utf-8
"""commands for selection"""
from controller.cli.command import Command
from model.control_desk import BankSet


def find_bank_set(identifier: str) -> BankSet | None:
    """
    find a bank set
    Args:
        identifier: the identifier of the bank set

    Returns:
        bank set or none if the identifier not exists
    """
    linked_sets = BankSet.get_linked_bank_sets()
    try:
        return linked_sets[int(identifier)]
    except:
        for bank_set in linked_sets:
            if bank_set.id == identifier:
                return bank_set
    return None


class SelectCommand(Command):

    def __init__(self, context):
        super().__init__(context, "select")
        self.help_text = "This command displays the help about a certain command."

    def configure_parser(self, parser):
        parser.add_argument("what", help="Specify what you would like to select")
        parser.add_argument("item", help="Specify the item you would like to select")

    def execute(self, args) -> bool:
        match args.what:
            case "scene":
                try:
                    scene_id = int(args.item)
                except:
                    self.context.print("Selected scene '{}' could not get parsed as integer id.".format(args.item))
                    return True
                candidate = self.context.show.get_scene_by_id(scene_id)
                if candidate is None:
                    self.context.print("No scene with id {} was found.".format(candidate))
                    return False
                self.context.selected_scene = candidate
                self.context.print("Selected scene '{}'.".format(candidate.human_readable_name))
                return True
            case "column":
                self.context.print("ERROR: Not yet implemented.")
                return False
            case "bank_set":
                found_bank_set = find_bank_set(args.item)
                if found_bank_set:
                    self.context.selected_bank = found_bank_set
                    return True
                else:
                    self.context.print(f"ERROR: the requested bank set '{args.item}' was not found")
            case _:
                self.context.print(
                    f"ERROR: The resource '{args.what}' cannot be selected. Type 'help select' to obtain a list.")
                return False
        return True
