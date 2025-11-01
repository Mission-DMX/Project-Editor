"""Contains fish connection management command."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui

from controller.cli.command import Command

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from controller.cli.cli_context import CLIContext


class FishConnCommand(Command):
    """Command to manage fish connection state."""

    def __init__(self, context: CLIContext) -> None:
        """Initialize command as 'fish'."""
        super().__init__(context, "fish")
        self._help_text = "Manage fish connection state."

    @override
    def configure_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument("action", choices=["connect", "disconnect", "query"],
                            help="The action to perform. Must be 'connect', 'disconnect' or 'query'.")

    @override
    def execute(self, args: Namespace) -> bool:
        match args.action:
            case "connect":
                if self.context.network_manager.connection_state():
                    return True
                self.context.network_manager.start()
                QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)
                return self.context.network_manager.connection_state()
            case "disconnect":
                self.context.network_manager.disconnect()
            case "query":
                if self.context.network_manager.connection_state():
                    self.context.print("Fish connected.")
                else:
                    self.context.print("Fish disconnected.")
        return True
