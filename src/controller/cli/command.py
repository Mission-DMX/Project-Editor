"""Client Commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from .cli_context import CLIContext


class Command(ABC):
    """Client Commands."""

    def __init__(self, cli_context: CLIContext, name: str) -> None:
        """Client Command.

        Args:
            cli_context: The context where the command should be registered with
            name: The name of the command

        """
        self.context = cli_context
        self._name = name
        self._help_text = ""

    @abstractmethod
    def configure_parser(self, parser: ArgumentParser) -> None:
        """Configure the parser.

        Args:
            parser: An argparse like parser

        """

    @abstractmethod
    def execute(self, args: Namespace) -> bool:
        """Execute a Command."""

    @property
    def name(self) -> str:
        """Name of the command."""
        if self._name:
            return self._name

        return "Unnamed Command"

    @property
    def help(self) -> str:
        """Help text."""
        return self._help_text

    @help.setter
    def help(self, new_help: str) -> None:
        self._help_text = str(new_help)
