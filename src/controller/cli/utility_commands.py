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
