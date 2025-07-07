"""commands for the Bank Sets"""
from controller.cli.command import Command
from model.control_desk import BankSet, ColorDeskColumn, FaderBank, RawDeskColumn


class BankSetCommand(Command):
    """
    commands for the Bank Sets
    """

    def __init__(self, context):
        super().__init__(context, "bank_set")
        self.help_text = "This command displays the help about a certain command."

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers(help="Specify what you would like to do", dest="what")
        subparsers.add_parser("commit", exit_on_error=False,
                              help="Commit the changes made to the bank set")
        create_parser = subparsers.add_parser("create", exit_on_error=False,
                                              help="Create a new bank set and make it the selected one")
        create_parser.add_argument('description', default="", type=str, nargs='?',
                                   help="Specify the human readable description of the bank set")
        add_parser = subparsers.add_parser("add", exit_on_error=False,
                                           help="Add a column to the specified bank in the selected bank set")
        add_parser.add_argument("--col-type", choices=["raw", "color"], default="color", nargs='?',
                                help="The type of the column to be created")
        add_parser.add_argument("--bank", type=int, default=-1, help="The bank to create the column on", nargs='?')
        add_parser.add_argument("--name", type=str, default="", nargs="?", help="Specify the displayed column name")
        subparsers.add_parser("info", exit_on_error=False, help="Display the selected bank set content")
        subparsers.add_parser("activate", exit_on_error=False, help="Activate the selected bank set")

    def execute(self, args) -> bool:
        """
        execute a Command with Arguments
        Args:
            args: the arguments

        Returns:
            True if executed without errors
        """
        match args.what:
            case "commit":
                if not self.context.selected_bank:
                    self.context.print("ERROR: No bank set selected.")
                    return False
                return self.context.selected_bank.update()
            case "create":
                if self.context.selected_bank:
                    if not self.context.selected_bank.is_linked:
                        self.context.print("ERROR: Creating a new bank set now would discard the changes made to the "
                                           "current selected one.")
                        return False
                self.context.selected_bank = BankSet([], description=args.description)
            case "add":
                if not self.context.selected_bank:
                    self.context.print("ERROR: No bank set selected. Create or select one first.")
                    return False
                if args.col_type == "raw":
                    col = RawDeskColumn()
                else:
                    col = ColorDeskColumn()
                if args.bank == len(self.context.selected_bank.banks):
                    self.context.selected_bank.banks.append(FaderBank())
                if args.bank > len(self.context.selected_bank.banks) or args.bank < -1:
                    self.context.print("ERROR: The selected bank is out of range.")
                    return False
                selected_bank = self.context.selected_bank.banks[int(args.bank)]
                if args.name == "":
                    col.display_name = str(len(selected_bank.columns))
                else:
                    col.display_name = args.name
                selected_bank.add_column(col)
            case "info":
                if not self.context.selected_bank:
                    self.context.print("ERROR: No bank set selected. Create or select one first.")
                    return False

                self.context.print(
                    f"The selected bank set contains {len(self.context.selected_bank.banks)} banks.")
                for bank_index, bank in enumerate(self.context.selected_bank.banks):
                    for column_index, column in enumerate(bank.columns):
                        col_type_str = "???"
                        if isinstance(column, ColorDeskColumn):
                            col_type_str = "HSI"
                        if isinstance(column, RawDeskColumn):
                            col_type_str = "RAW"
                        self.context.print(
                            str(bank_index) + "/" + str(column_index) + " " + col_type_str + " " + column.display_name)

            case "activate":
                if not self.context.selected_bank:
                    self.context.print("ERROR: No bank set selected. Create or select one first.")
                    return False

                self.context.selected_bank.activate()
            case _:
                self.context.print(
                    f"ERROR: The subcommand '{args.what}' is not known. Type 'help bank_set' to obtain a list.")
                return False
        return True
