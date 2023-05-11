from cli.command import Command

class ListCommand(Command):

    def __init__(self, context):
        super().__init__(context, "list")
        self.help_text = "This command displays the content of system collections."

    def configure_parser(self, parser):
        pass

    def execute(self, args) -> str:
        pass
