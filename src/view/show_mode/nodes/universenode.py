# coding=utf-8
"""Universe filter node"""
from model import Filter, DataType
from . import FilterNode


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = 'Universe'

    universe_ids: list[int] = []

    def __init__(self, name):
        super().__init__(filter_type=11, name=name, terminals={
            "input_1": {'io': 'in'}
        }, allow_add_input=True)

        self.filter.filter_configurations["universe"] = self.name()[9:]
        self.filter.filter_configurations["input_1"] = "0"
        self._in_value_types = {f"input_{i}": DataType.DT_8_BIT for i in range(1, 513)}

    def addInput(self, name="input", **args):
        """Allows to add up to 512 input channels."""
        next_input = len(self.inputs())
        if next_input >= 512:
            return None
        input_channel = f"input_{next_input + 1}"
        self.filter.filter_configurations[input_channel] = str(next_input)
        return super().addInput(input_channel, **args)

    def removeTerminal(self, term):
        if term.isInput():
            del self.filter.filter_configurations[term.name()]
        return super().removeTerminal(term)

    def setup_filter(self, filter_: Filter = None):
        super().setup_filter(filter_)
        if filter_ is not None:
            for _ in range(len(filter_.channel_links) - 1):
                self.addInput()
