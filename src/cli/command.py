from abc import ABC, abstractmethod

class Command(ABC):
    def __init__(self, cli_context, name: str):
        self.context = cli_context
        self.name = name
        self.help_text = ""

    @abstractmethod
    def configure_parser(self, parser):
        """This method will be called by the CLI context in order to configure the parser

        Arguments:
        parser -- An argparse like parser
        """
        pass

    @abstractmethod
    def execute(self, args) -> bool:
        pass

    def get_name(self) -> str:
        if self.name:
            return self.name
        else:
            return "Unnamed Command"

    def get_help(self) -> str:
        return self.help_text
