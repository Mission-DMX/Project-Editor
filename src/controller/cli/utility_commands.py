from enum import Enum
from time import sleep
from typing import TYPE_CHECKING

from controller.cli.command import Command

if TYPE_CHECKING:
    from argparse import ArgumentParser


class DelayCommand(Command):
    def __init__(self, context):
        super().__init__(context, "delay")

    def configure_parser(self, parser: "ArgumentParser"):
        parser.add_argument("delay", type=int, help="Delay in milliseconds")

    def execute(self, args) -> bool:
        try:
            sleep(args.delay / 1000)
            return True
        except ValueError as e:
            self.context.print(f"Unable to sleep on specified interval: {e}")
            return False


class PrintCommand(Command):
    def __init__(self, context):
        super().__init__(context, "print")

    def configure_parser(self, parser: "ArgumentParser"):
        parser.add_argument("text", type=str, help="Stuff to print", nargs="*")

    def execute(self, args) -> bool:
        text = " ".join(args.text)
        self.context.print(text)
        return True


class SetCommand(Command):
    def __init__(self, context):
        super().__init__(context, "set")

    def configure_parser(self, parser: "ArgumentParser"):
        parser.add_argument("key", type=str, help="The variable to set")
        parser.add_argument("value", type=str, help="The value to set it to")

    def execute(self, args) -> bool:
        self.context.variables[args.key] = args.value
        # TODO implement support for arithmetic in case of numbers
        return True


class _CmpMode(Enum):
    EQUALS = 0
    GT = 1
    LT = 2
    NOT_EQUALS = 3
    AND = 4
    OR = 5


class IfCommand(Command):
    def __init__(self, context):
        super().__init__(context, "if")

    def configure_parser(self, parser: "ArgumentParser"):
        parser.add_argument("expression", type=str, help="The expression to evaluate", nargs="*")

    def execute(self, args) -> bool:
        def bool_eval(arg: str):
            return len(arg) > 0 and not arg == "0"

        in_command = False
        found_split = False
        cmp_mode = _CmpMode.AND
        command = []
        rhs = ""
        for arg in args.expression:
            if in_command:
                command.append(arg)
                continue
            if arg == "then":
                in_command = True
            elif arg == "=":
                found_split = True
                cmp_mode = _CmpMode.EQUALS
            elif arg == "!=":
                found_split = True
                cmp_mode = _CmpMode.NOT_EQUALS
            elif arg == ">":
                found_split = True
                cmp_mode = _CmpMode.GT
            elif arg == "<":
                found_split = True
                cmp_mode = _CmpMode.LT
            elif arg == "and":
                found_split = True
                cmp_mode = _CmpMode.AND
            elif arg == "or":
                found_split = True
                cmp_mode = _CmpMode.OR
            elif found_split:
                found_split = False
                match cmp_mode:
                    case _CmpMode.LT:
                        try:
                            rhs = "1" if float(rhs) < float(arg) else "0"
                        except ValueError:
                            self.context.print(f"Error: cannot evaluate {rhs} < {arg}")
                            rhs = "0"
                    case _CmpMode.GT:
                        try:
                            rhs = "1" if float(rhs) > float(arg) else "0"
                        except ValueError:
                            self.context.print(f"Error: cannot evaluate {rhs} > {arg}")
                            rhs = "0"
                    case _CmpMode.EQUALS:
                        rhs = "1" if rhs == arg else "0"
                    case _CmpMode.NOT_EQUALS:
                        rhs = "1" if rhs != arg else "0"
                    case _CmpMode.AND:
                        rhs = "1" if bool_eval(rhs) and bool_eval(arg) else "0"
                    case _CmpMode.OR:
                        rhs = "1" if bool_eval(rhs) or bool_eval(arg) else "0"
            else:
                rhs = arg
        if bool_eval(rhs):
            return self.context.exec_command(" ".join(command))
        else:
            return True
