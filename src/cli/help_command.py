from cli.command import Command

class HelpCommand(Command):

    def __init__(self, context):
        super().__init__(context, "help")
        self.help_text = "This command displays the help about a certain command."

    def configure_parser(self, parser):
        parser.add_argument("topic", help="Specify the topic you like to hear about")

    def execute(self, args) -> bool:
        match args.topic:
            case "select":
                self.context.print("Use this command to alter the selected regions within this context.")
                self.context.print("The following defaults can be changed:")
                self.context.print("\tscene -- Select the scene to perform actions on")
                self.context.print("\tcolumn -- Select the control desk column to perform actions on")
                self.context.print("\tbankset -- Select the control desk bank set to perform actions on")
            case _:
                self.context.print("The requested help topic '{}' is unknown.".format(args.topic))
                self.context.print("The following topics are known:")
                self.context.print("\tselect")
