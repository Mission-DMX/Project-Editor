import argparse

class CLIContext():
    def __init__():
        self.commands = []
        self.selected_bank = None # TODO query avaiable banks
        self.selected_column = None # TODO query available columns
        self.selected_scene = None # TODO query avaiable scenes
        pass

    def exec_command(line: str) -> bool:
        """Execute a command within the given context
        Arguments:
        line -- the command to be parsed and executed

        Returns:
        true if the evaluation succeeded, false otherwise
        """
        pass
