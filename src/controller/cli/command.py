# coding=utf-8
"""Client Commands"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cli_context import CLIContext


class Command(ABC):
    """Client Commands"""

    def __init__(self, cli_context: "CLIContext", name: str):
        """
        Create a new command.
        :param cli_context: The context where the command should be registered with
        :param name: The name of the command
        """
        self.context = cli_context
        self._name = name
        self._help_text = ""

    @abstractmethod
    def configure_parser(self, parser):
        """This method will be called by the CLI context in order to configure the parser

        Arguments:
        parser -- An argparse like parser
        """

    @abstractmethod
    def execute(self, args) -> bool:
        """execute a Command"""

    @property
    def name(self) -> str:
        """
        name of the command
        Returns:
            the name or 'unnamed Command' if none is set
        """
        if self._name:
            return self._name

        return "Unnamed Command"

    @property
    def help(self) -> str:
        """ help text"""
        return self._help_text
