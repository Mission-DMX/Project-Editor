from typing import TYPE_CHECKING

from controller.cli.command import Command

if TYPE_CHECKING:
    from argparse import ArgumentParser

    from controller.cli.cli_context import CLIContext


class MacroCommand(Command):
    def __init__(self, context: "CLIContext"):
        super().__init__(context, "macro")

    def configure_parser(self, parser: "ArgumentParser"):
        subparsers = parser.add_subparsers(help="macro commands", dest="macroaction")
        exec_parser: "ArgumentParser" = subparsers.add_parser("exec", help="Execute a macro", exit_on_error=False)
        exec_parser.add_argument("macro", help="The macro to execute")
        # TODO implement export sub command
        # TODO implement import sub command
        # TODO implement create sub command
        # TODO implement rename sub command
        # TODO implement append sub command
        pass

    def execute(self, args) -> bool:
        match args.macroaction:
            case "exec":
                if args.macro in self.context.stack:
                    self.context.print(f"ERROR: The macro '{args.macro}' is already in call stack. Recursion is not supported.")
                    return False
                for m in self.context.show.macros:
                    if m.name == args.macro:
                        self.context.stack.add(m.name)
                        m.c.return_text = ""
                        res = m.exec()
                        if len(m.c.return_text) > 0:
                            self.context.print(m.c.return_text)
                        self.context.stack.discard(m.name)
                        return res
                self.context.print(f"ERROR: Macro '{args.macro}' not found.")
                return False
            case _:
                self.context.print("Unknown macro action")