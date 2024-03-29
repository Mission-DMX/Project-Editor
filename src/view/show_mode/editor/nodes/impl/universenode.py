# coding=utf-8
"""Universe filter node"""
from logging import getLogger

from pyqtgraph.flowchart import Terminal

from model import DataType, Filter
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__name__)


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = 'Universe'

    universe_ids: list[int] = []

    def __init__(self, model, name):
        if isinstance(model, Filter):
            super().__init__(model=model, filter_type=11, name=name, terminals={
                input_link: {'io': 'in'} for input_link, _ in model.channel_links.items()},
                             allowAddInput=True)
        else:
            super().__init__(model=model, filter_type=11, name=name, terminals={
                "input_1": {'io': 'in'}},
                             allowAddInput=True)

        try:
            if len(model.filter_configurations) == 0:
                self.filter.filter_configurations["input_1"] = "0"
                self.filter.in_data_types["input_1"] = DataType.DT_8_BIT
                self.filter.filter_configurations["universe"] = str(int(self.name()[9:]) + 1)
            else:
                for key in self.filter.filter_configurations.keys():
                    if self.filter != model:
                        self.filter.filter_configurations[key] = model.filter_configurations[key]
                    if key != "universe":
                        input_channel = key
                        self.filter.in_data_types[input_channel] = DataType.DT_8_BIT
                        if key not in self.terminals.keys():
                            term = super().addInput(key)
                        else:
                            t: Terminal = self.terminals[key]
                            if not t.isInput():
                                logger.error("Universe output filter '{}' has corrupted terminal '{}'."
                                             .format(self.name(), input_channel))
        except:
            self.filter.filter_configurations["input_1"] = "0"
            self.filter.in_data_types["input_1"] = DataType.DT_8_BIT
            self.filter.filter_configurations["universe"] = str(int(self.name()[9:]) + 1)

    def addInput(self, name="input", **args):
        """Allows to add up to 512 input channels."""
        next_input = len(self.inputs())
        if next_input >= 512:
            return
        input_channel = f"{name}_{next_input + 1}"
        self.filter.filter_configurations[input_channel] = str(next_input)
        self.filter.in_data_types[input_channel] = DataType.DT_8_BIT
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
