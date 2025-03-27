# coding=utf-8
"""Context of the Client"""
import argparse
import traceback
from typing import TYPE_CHECKING

from controller.cli.bankset_command import BankSetCommand
from controller.cli.help_command import HelpCommand
from controller.cli.list_command import ListCommand
from controller.cli.select_command import SelectCommand
from controller.cli.show_command import ShowCommand

if TYPE_CHECKING:
    from controller.network import NetworkManager
    from model import BoardConfiguration, Scene
    from model.control_desk import BankSet, DeskColumn


class CLIContext:
    """Context of the Client"""

    def __init__(self, show: "BoardConfiguration", networkmgr: "NetworkManager", exit_available: bool = False):
        """
        Initialize a new CLI context.
        :param show: The current active show configuration
        :param networkmgr: The active network manager, user for communication with fish
        :param exit_available: Should the exit command (close the connection) be available or not?
        """
        self.commands = [
            ListCommand(self),
            SelectCommand(self),
            BankSetCommand(self),
            ShowCommand(self),
            HelpCommand(self)
        ]
        self.selected_bank: "BankSet" | None = None
        self.selected_column: "DeskColumn" | None = None
        self.selected_scene: "Scene" | None = None
        self.show = show
        self.networkmgr: "NetworkManager" = networkmgr
        self.parser = argparse.ArgumentParser(exit_on_error=False)
        subparsers = self.parser.add_subparsers(help='subcommands help', dest="subparser_name")
        for c in self.commands:
            c.configure_parser(subparsers.add_parser(c.name, help=c.help, exit_on_error=False))
        if exit_available:
            subparsers.add_parser("exit", exit_on_error=False, help="Close this remote connection")
        self.return_text = ""
        self.exit_called = False
        self._exit_available = exit_available

    def exec_command(self, line: str) -> bool:
        """Execute a command within the given context
        Arguments:
        line -- the command to be parsed and executed

        Returns:
        true if the evaluation succeeded, false otherwise
        """
        try:
            global_args = self.parser.parse_args(args=line.split(" "))
            if self._exit_available and global_args.subparser_name == "exit":
                self.exit_called = True
            elif global_args.subparser_name == "?":
                self.print(self.parser.format_help())
            else:
                for c in self.commands:
                    if c.name == global_args.subparser_name:
                        return c.execute(global_args)
        except argparse.ArgumentError as e:
            self.print("Failed to parse command: " + str(e))
            self.print(self.parser.format_usage())
        except Exception as e:
            self.print(traceback.format_exc())
            self.print("Execution of command failed: " + str(e))
        return False

    def print(self, text: str):
        """This method can be used by commands to print text to which ever output medium there is.

        Arguments:
        text -- The line to be printed
        """
        self.return_text += text + '\n'

    def fetch_print_buffer(self) -> str:
        """This method returns the stored output buffer and clears it.

        Returns:
        The stored text that was accumulated by print.
        """
        tmp_text = self.return_text
        self.return_text = ""
        return tmp_text
