"""Context of the Client."""

from __future__ import annotations

import argparse
import traceback
from argparse import Namespace
from types import MappingProxyType
from typing import TYPE_CHECKING

from controller.cli.asset_command import AssetCommand
from controller.cli.bankset_command import BankSetCommand
from controller.cli.event_command import EventCommand
from controller.cli.help_command import HelpCommand
from controller.cli.list_command import ListCommand
from controller.cli.macro_command import MacroCommand
from controller.cli.select_command import SelectCommand
from controller.cli.show_command import ShowCommand
from controller.cli.utility_commands import DelayCommand, IfCommand, PrintCommand, SetCommand

if TYPE_CHECKING:
    from controller.network import NetworkManager
    from model import BoardConfiguration, Scene
    from model.control_desk import BankSet


def _split_args(line: str) -> list[str]:
    """Split a line into individual arguments."""
    argument_list: list[str] = []
    in_string: bool = False
    current_arg = ""
    in_escape: bool = False
    for c in line:
        if in_string:
            if c == '"' and not in_escape:
                in_string = False
                continue
            if c == "\\":
                in_escape = not in_escape
            if not in_escape:
                current_arg += c
            else:
                match c:
                    case "t":
                        current_arg += "\t"
                        in_string = False
                    case "n":
                        current_arg += "\n"
                        in_escape = False
                    case "r":
                        current_arg += "\r"
                        in_escape = False
                    case "$":
                        current_arg += "\\$"
                        in_escape = False
                    case '"':
                        current_arg += c
                        in_escape = False
        else:
            if c == '"':
                in_string = True
                in_escape = False
            elif c == "#":
                if current_arg != "":
                    argument_list.append(current_arg)
                break
            elif c in (" ", "\t"):
                if current_arg != "":
                    argument_list.append(current_arg)
                    current_arg = ""
            else:
                current_arg += c
    if current_arg != "":
        argument_list.append(current_arg)
    return argument_list


class CLIContext:
    """Context of the Client."""

    def __init__(self, show: BoardConfiguration, network_manager: NetworkManager, exit_available: bool = False) -> None:
        """Initialize a new CLI context.

        Args:
            show: The current active show configuration
            network_manager: The active network manager, user for communication with fish
            exit_available: Should the exit command (close the connection) be available or not?

        """
        self._commands = [
            ListCommand(self),
            SelectCommand(self),
            BankSetCommand(self),
            ShowCommand(self),
            EventCommand(self),
            DelayCommand(self),
            MacroCommand(self),
            PrintCommand(self),
            SetCommand(self),
            IfCommand(self),
            HelpCommand(self),
            AssetCommand(self),
        ]
        self._selected_bank: BankSet | None = None
        self._selected_scene: Scene | None = None
        self._stack = set()
        self._variables: dict[str, str] = {}
        self._show = show
        self._network_manager: NetworkManager = network_manager
        self._parser = argparse.ArgumentParser(exit_on_error=False)
        subparsers: argparse._SubParsersAction = self._parser.add_subparsers(
            help="subcommands help", dest="subparser_name"
        )
        for c in self._commands:
            c.configure_parser(subparsers.add_parser(c.name, help=c.help, exit_on_error=False))
        if exit_available:
            subparsers.add_parser("exit", exit_on_error=False, help="Close this remote connection")
        self._return_text = ""
        self._exit_called = False
        self._exit_available = exit_available

    @property
    def exit_called(self) -> bool:
        """Return whether the exit command has been called."""
        return self._exit_called

    @exit_called.setter
    def exit_called(self, new_exit_called: bool) -> None:
        self._exit_called = new_exit_called

    @property
    def return_text(self) -> str:
        """Return text."""
        return self._return_text

    @return_text.setter
    def return_text(self, new_return_text: str) -> None:
        self._return_text = new_return_text

    @property
    def network_manager(self) -> NetworkManager:
        """Network manager."""
        return self._network_manager

    @property
    def show(self) -> BoardConfiguration:
        """Current show configuration."""
        return self._show

    @property
    def variables(self) -> MappingProxyType[str, str]:
        """Variables."""
        return MappingProxyType(self._variables)

    def update_variables(self, new_variables: dict[str, str]) -> None:
        """Update the variables."""
        self._variables.update(new_variables)

    @property
    def stack(self) -> frozenset[str]:
        """Stack of commands."""
        return frozenset(self._stack)

    def add_to_stack(self, command: str) -> None:
        """Add a command to the stack."""
        self._stack.add(command)

    def discard_from_stack(self, command: str) -> None:
        """Remove a command from the stack."""
        self._stack.discard(command)

    @property
    def selected_scene(self) -> Scene | None:
        """Currently selected scene."""
        return self._selected_scene

    @selected_scene.setter
    def selected_scene(self, new_selected_scene: Scene) -> None:
        self._selected_scene = new_selected_scene

    @property
    def selected_bank(self) -> BankSet | None:
        """Currently selected bank."""
        return self._selected_bank

    @selected_bank.setter
    def selected_bank(self, new_selected_bank: BankSet) -> None:
        self._selected_bank = new_selected_bank

    def _replace_variables(self, args: list[str]) -> list[str]:
        """Replace variables in the provided list of arguments with their current values.

        Args:
            args: The list of arguments.

        Returns:
            The list of arguments with resolved variables.

        """
        new_arg_list = []
        for arg in args:
            if arg.startswith("\\$"):
                new_arg_list.append(arg[1:])
            elif arg.startswith("$"):
                new_arg_list.append(str(self._variables.get(arg[1:])))
            else:
                new_arg_list.append(arg)
        return new_arg_list

    def exec_command(self, line: str) -> bool:
        """Execute a command within the given context.

        Args:
            line: The command to be parsed and executed.

        Returns: True if the evaluation succeeded, False otherwise.

        """
        try:
            args = _split_args(line)
            args = self._replace_variables(args)
            if len(args) == 0:
                return True
            try:
                global_args: Namespace = self._parser.parse_args(args=args)
            except SystemExit:
                self.print(f"Syntax error. Failed to parse arguments. Args: {args}")
                self.print("Usage:")
                self.print(self._parser.format_help().replace("usage: main.py [-h]", "", 1))
                return False
            if self._exit_available and global_args.subparser_name == "exit":
                self._exit_called = True
            elif global_args.subparser_name == "?":
                self.print(self._parser.format_help())
            else:
                for c in self._commands:
                    if c.name == global_args.subparser_name:
                        return c.execute(global_args)
        except argparse.ArgumentError as e:
            self.print("Failed to parse command: " + str(e))
            self.print(self._parser.format_usage())
        except Exception as e:
            self.print(traceback.format_exc())
            self.print("Execution of command failed: " + str(e))
        return False

    def print(self, text: str) -> None:
        """Print text to the available output medium.

        Args:
            text: The line to be printed.

        """
        self._return_text += text + "\n"

    def fetch_print_buffer(self) -> str:
        """Get the output buffer and clear it.

        Returns:
            The stored text that print accumulated.

        """
        tmp_text = self._return_text
        self._return_text = ""
        return tmp_text
