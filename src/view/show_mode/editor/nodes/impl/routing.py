from __future__ import annotations

from logging import getLogger
from typing import override

from model import DataType
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__name__)

class SwitchFilterNode(FilterNode):
    """Base class to represent abstract switch filter."""

    def __init__(self, model: Filter, name: str, filter_type: int, data_type: DataType) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=filter_type,
            name=name,
            allow_add_output=True,
            terminals={
                "out": {"io": "out"},
                "select": {"io": "in"}
            },
        )

        self._filter.in_data_types["select"] = DataType.DT_16_BIT
        self._filter.in_data_types["out"] = data_type
        self._filter.default_values["select"] = "0"

        if not self._filter.filter_configurations.get("nr_inputs"):
            self._filter.filter_configurations["nr_inputs"] = "2"

        self._data_type = data_type
        self._setup_input_terminals()

    def _setup_input_terminals(self) -> None:
        existing_inputs = list(self.inputs())
        try:
            required_input_count = int(self._filter.filter_configurations["nr_inputs"])
        except ValueError:
            logger.error("Invalid number of inputs: %s. Resetting to 0.", len(self._filter.filter_configurations))
            required_input_count = 0
            self._filter.filter_configurations["nr_inputs"] = "0"
        if required_input_count < 0:
            logger.error("Invalid number of inputs: %s. Resetting to 0.", required_input_count)
            required_input_count = 0
            self._filter.filter_configurations["nr_inputs"] = "0"
        for input_key in existing_inputs:
            if input_key != "select" and int(input_key) >= required_input_count:
                self.removeTerminal(input_key)
        existing_inputs = list(self.inputs())
        for i in range(required_input_count):
            key = str(i)
            if key not in existing_inputs:
                self.addInput(key)
                self._filter.in_data_types[key] = self._data_type
                self._filter.default_values[key] = "0,0,0" if self._data_type == DataType.DT_COLOR else "0"

    @override
    def update_node_after_settings_changed(self) -> None:
        self._setup_input_terminals()

class Switch8BitNode(SwitchFilterNode):
    """8 bit switch filter node implementation."""

    nodeName = "filter_switch_8bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_8BIT, DataType.DT_8_BIT)

class Switch16BitNode(SwitchFilterNode):
    """16 bit switch filter node implementation."""

    nodeName = "filter_switch_16bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_16BIT, DataType.DT_16_BIT)

class SwitchFloatNode(SwitchFilterNode):
    """Float switch filter node implementation."""

    nodeName = "filter_switch_float"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_FLOAT, DataType.DT_DOUBLE)

class SwitchColorNode(SwitchFilterNode):
    """8 bit switch filter node implementation."""

    nodeName = "filter_switch_color"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_COLOR, DataType.DT_COLOR)
