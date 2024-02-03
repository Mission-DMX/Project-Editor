# coding=utf-8
"""Client Commands"""
from controller.cli.command import Command
from model.control_desk import BankSet


class ListCommand(Command):

    def __init__(self, context):
        super().__init__(context, "list")
        self.help_text = "This command displays the content of system collections."

    def configure_parser(self, parser):
        parser.add_argument("section", help="The section of which content should be listed")

    def execute(self, args) -> bool:
        match args.section:
            case "scenes":
                self.context.print("ERROR: Listing the loaded scenes is not yet implemented.")
                return False
            case "filters":
                self.context.print("ERROR: Listing the filters of the current selected scene isn't yet implemented.")
                return False
            case "columns":
                self.context.print("ERROR: Listing the columns within the selected bank set is not yet implemented.")
                return False
            case "bank_sets":
                self.context.print(" Bank Set ID                         | Description ")
                self.context.print("===================================================")
                selected_bank_set_id = self.context.selected_bank if self.context.selected_bank else ""
                for bs in BankSet.get_linked_bank_sets():
                    self.print_bank_set_entry(bs, selected_bank_set_id)
                if self.context.selected_bank and not self.context.selected_bank.is_linked:
                    self.print_bank_set_entry(self.context.selected_bank, selected_bank_set_id)
                return True
            case _:
                self.context.print("ERROR: The requested container '{}' was not found.".format(args.section))
                return False

    def print_bank_set_entry(self, bs, selected_bank_set_id):
        """print the entry of a bank set"""
        preamble = "*" if bs.id == selected_bank_set_id else " "
        if bs.is_linked:
            self.context.print(preamble + bs.id + " | " + bs.description)
        else:
            self.context.print(preamble + "Warning: Not yet linked.         | " + bs.description)
