from cli.command import Command
from model.control_desk import BankSet, RawDeskColumn, ColorDeskColumn


class BanksetCommand(Command):

    def __init__(self, context):
        super().__init__(context, "bankset")
        self.help_text = "This command displays the help about a certain command."

    def configure_parser(self, parser):
        parser.add_argument("what", help="Specify what you would like to do")
        parser.add_argument("first_arg", optional=True)
        parser.add_argument("second_arg", optional=True)

    def execute(self, args) -> bool:
        match args.what:
            case "commit":
                if not self.context.selected_bank:
                    self.context.print("ERROR: No bank set selected.")
                    return False
                self.context.selected_bank.update()
            case "create":
                if self.context.selected_bank:
                    if not self.context.selected_bank.is_linked:
                        self.context.print("ERROR: Creating a new bank set now would discard the changes made to the "
                                           "current selected one.")
                        return False
                self.context.selected_bank = BankSet([], description=args.first_arg)
            case "add":
                if not self.context.selected_bank:
                    self.context.print("ERROR: No bank set selected. Create or select one first.")
                    return False
                col = None
                if args.second_arg == "raw":
                    col = RawDeskColumn()
                else:
                    col = ColorDeskColumn()
                self.context.selected_bank.banks[int(args.first_arg)].add_column(col)
            case _:
                self.context.print("ERROR: The subcommand '{}' is not known. Type 'help bankset' to obtain a list."
                                   .format(args.what))
                return False
        return True
