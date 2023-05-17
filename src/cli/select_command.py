# coding=utf-8
"""commands for selection"""
from cli.command import Command
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
        for bs in linked_sets:
            if bs.id == identifier:
                return bs
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
                self.context.print("ERROR: Not yet implemented.")
            case "column":
                self.context.print("ERROR: Not yet implemented.")
            case "bank_set":
                found_bank_set = find_bank_set(args.item)
                if found_bank_set:
                    self.context.selected_bank = found_bank_set
                    return True
                else:
                    self.context.print("ERROR: the requested bank set '{}' was not found".format(args.item))
            case _:
                self.context.print("ERROR: The resource '{}' cannot be selected. Type 'help select' to obtain a list."
                                   .format(args.what))
                return False
        return True
