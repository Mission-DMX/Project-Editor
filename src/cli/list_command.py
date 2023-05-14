from cli.command import Command
from model.control_desk import BankSet

class ListCommand(Command):

    def __init__(self, context):
        super().__init__(context, "list")
        self.help_text = "This command displays the content of system collections."

    def configure_parser(self, parser):
        parser.add_argument("section", help="The section of which content should be listed")

    def execute(self, args) -> str:
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
            case "banksets":
                self.context.print("Bank Set ID                      | Description ")
                self.context.print("===============================================")
                for bs in BankSet.get_linked_bank_sets():
                    self.context.print(bs.id + " | " + bs.description)
                return False
            case _:
                self.context.print("ERROR: The requested container '{}' was not found.".format(args.section))
                return False
        return True
