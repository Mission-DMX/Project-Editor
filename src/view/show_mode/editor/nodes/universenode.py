# coding=utf-8
"""Universe filter node"""
from model import DataType, Filter
from . import FilterNode


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = 'Universe'

    universe_ids: list[int] = []

    def __init__(self, model, name):
        if isinstance(model, Filter):
            super().__init__(model=model, filter_type=11, name=name, terminals={
                input_link: {'io': 'in'} for input_link, _ in model.channel_links.items()
            })
        else:
            super().__init__(model=model, filter_type=11, name=name, terminals={
                "input_1": {'io': 'in'}
            })
        self._allowAddInput = True

        self.filter.filter_configurations["universe"] = self.name()[9:]
        self.filter.filter_configurations["input_1"] = "0"
        self._in_value_types = {f"input_{i}": DataType.DT_8_BIT for i in range(1, 513)}

    def addInput(self, name="input", **args):
        """Allows to add up to 512 input channels."""
        next_input = len(self.inputs())
        if next_input >= 512:
            return
        input_channel = f"input_{next_input + 1}"
        self.filter.filter_configurations[input_channel] = str(next_input)
        term = super().addInput(input_channel, **args)
        universe_id = int(self._filter.filter_configurations["universe"])
        universe = self._filter.scene.board_configuration.universe(universe_id)
        for channel in universe.patching:
            if next_input == channel.address:
                term.rename(f"{term.name} : {channel.fixture.short_name}")

    def removeTerminal(self, term):
        if term.isInput():
            del self.filter.filter_configurations[term.name()]
        return super().removeTerminal(term)
