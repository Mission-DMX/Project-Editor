"""Universe filter node"""
from logging import getLogger
from typing import Any, override

from pyqtgraph.flowchart import Terminal

from model import DataType, Filter, Scene
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__name__)


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = "Universe"  # noqa: N815

    universe_ids: list[int] = []

    def __init__(self, model: Filter | Scene, name: str) -> None:
        if isinstance(model, Filter):
            super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT, name=name,
                             terminals={
                                 input_link: {"io": "in"} for input_link, _ in model.channel_links.items()},
                             allow_add_input=True)
        else:
            super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT, name=name,
                             terminals={
                                 "input_1": {"io": "in"}},
                             allow_add_input=True)

        try:
            if len(model.filter_configurations) == 0:
                self.filter.filter_configurations["input_1"] = "0"
                self.filter.in_data_types["input_1"] = DataType.DT_8_BIT
                self.filter.filter_configurations["universe"] = str(int(self.name()[9:]) + 1)
            else:
                for key in self.filter.filter_configurations:
                    if self.filter != model:
                        self.filter.filter_configurations[key] = model.filter_configurations[key]
                    if key != "universe":
                        input_channel = key
                        self.filter.in_data_types[input_channel] = DataType.DT_8_BIT
                        if key not in self.terminals:
                            super().addInput(key)
                        else:
                            t: Terminal = self.terminals[key]
                            if not t.isInput():
                                logger.error("Universe output filter '%s' has corrupted terminal '%s'."
                                             , self.name(), input_channel)
        except:
            self.filter.filter_configurations["input_1"] = "0"
            self.filter.in_data_types["input_1"] = DataType.DT_8_BIT
            self.filter.default_values["input_1"] = "0"
            self.filter.filter_configurations["universe"] = str(int(self.name()[9:]) + 1)

    @override
    def addInput(self, name: str = "input", **args: dict[str, Any]) -> None:
        """Allows to add up to 512 input channels."""
        next_input = len(self.inputs())
        if next_input >= 512:
            return
        input_channel = f"{name}_{next_input + 1}"
        self.filter.filter_configurations[input_channel] = str(next_input)
        in_term_name = self.nextTerminalName(input_channel)
        self.filter.in_data_types[in_term_name] = DataType.DT_8_BIT
        self.filter.default_values[in_term_name] = "0"
        # term =(
        super().addInput(input_channel, **args)
        # Todo: good idea to rename the device (and maybe the channel) to the terminal,
        #  but should get updated if the configuration has changed, and error ..?
        # )
        # universe_id = int(self._filter.filter_configurations["universe"])
        # universe = self._filter.scene.board_configuration.universe(universe_id)
        # for channel in universe.patching:
        #     print(term)
        #     print(term.name())
        #     if next_input == channel.address:
        #         new_name = f"{term.name()} : {channel.fixture.short_name
        #                                             if channel.fixture.short_name != '' else channel.fixture.name}"
        #         self.filter.in_data_types[new_name] = DataType.DT_8_BIT
        #         term.rename(new_name)

        # print("Universe add input")
        # # self.super().super().addInput(name="test23")
        # self.filter.in_data_types["test23"] = DataType.DT_8_BIT
        # return term

    @override
    def removeTerminal(self, term: Terminal) -> None:
        if term.isInput():
            del self.filter.filter_configurations[term.name()]
        super().removeTerminal(term)
