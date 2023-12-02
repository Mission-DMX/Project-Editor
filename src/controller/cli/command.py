# coding=utf-8
"""Client Commands"""
from abc import ABC, abstractmethod


class Command(ABC):
    """Client Commands"""

    def __init__(self, cli_context, name: str):
        self.context = cli_context
        self._name = name
        self._help_text = ""

    @abstractmethod
    def configure_parser(self, parser):
        """This method will be called by the CLI context in order to configure the parser

        Arguments:
        parser -- An argparse like parser
        """
        pass

    @abstractmethod
    def execute(self, args) -> bool:
        """execute a Command"""
        pass

    @property
    def name(self) -> str:
        """
        name of the command
        Returns:
            the name or 'unnamed Command' if none is set
        """
        if self._name:
            return self._name
        else:
            return "Unnamed Command"

    @property
    def help(self) -> str:
        """ help text"""
        return self._help_text
