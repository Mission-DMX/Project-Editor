"""Universe filter node"""
from logging import getLogger
from typing import Any, ClassVar, override

from pyqtgraph.flowchart import Terminal

from model import Filter, Scene
from model.filter import FilterTypeEnumeration
from model.universe import NUMBER_OF_CHANNELS
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__name__)


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = "Universe"  # noqa: N815

    universe_ids: ClassVar[list[int]] = []

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(
            model=model, filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT, name=name, allow_add_input=True
        )
        # Fresh-creation path: the backing filter arrives with no configuration, so seed the
        # universe id (derived from the node name by convention) and a default first input,
        # then re-sync pyqtgraph terminals from the newly-populated model signature.
        if "universe" not in self.filter.filter_configurations:
            try:
                self.filter.filter_configurations["universe"] = str(int(name[9:]) + 1)
            except (ValueError, IndexError):
                self.filter.filter_configurations["universe"] = "1"
        if not self.filter.in_data_types:
            self.filter.filter_configurations["input_1"] = "0"
            self.update_node_after_settings_changed()

    @override
    def addInput(self, name: str = "input", **args: dict[str, Any]) -> None:
        """Allows adding up to 512 input channels.

        Two call sites hit this:

        * Interactive add from pyqtgraph's "+" affordance. ``name`` is the generic default and
          not yet in the model's configuration; we generate a unique channel name, assign the
          next free DMX index, and let the model's ``_rebuild_io`` pick up the terminal.
        * Base-class terminal sync from :meth:`FilterNode.update_node_after_settings_changed`.
          ``name`` matches an existing configuration key; just surface it in pyqtgraph.
        """
        if name in self.filter.filter_configurations:
            super().addInput(name, **args)
            return
        next_input = len(self.inputs())
        if next_input >= NUMBER_OF_CHANNELS:
            return
        input_channel = f"{name}_{next_input + 1}"
        in_term_name = self.nextTerminalName(input_channel)
        self.filter.update_filter_configuration(in_term_name, str(next_input))
        super().addInput(in_term_name, **args)

    @override
    def removeTerminal(self, term: Terminal) -> None:
        if term.isInput() and term.name() in self.filter.filter_configurations:
            del self.filter.filter_configurations[term.name()]
            self.filter._rebuild_io()
        super().removeTerminal(term)
