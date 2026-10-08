"""Filter Nodes for effect filters."""

from typing import override

from model import DataType, Scene
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class CueListNode(FilterNode):
    """Filter node to represent a cue filter."""

    nodeName = "Cues"  # noqa: N815 nodeName Required for FilterNode

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            name=name,
            allow_add_output=True,
        )
        self.channel_hints["time"] = " [ms]"


class ShiftFilterNode(FilterNode):
    """Filter node to represent an abstract shift filter."""

    def __init__(self, model: Filter, name: str, id_: int) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=id_, name=name, allow_add_output=True)
        self.channel_hints["switch_time"] = " [ms]"
        self.channel_hints["time"] = " [ms]"


class Shift8BitNode(ShiftFilterNode):
    """Filter node to represent a shift 8-bit filter."""

    nodeName = "filter_shift_8bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT)


class Shift16BitNode(ShiftFilterNode):
    """Filter node to represent a shift 16-bit filter."""

    nodeName = "filter_shift_16bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_16BIT)


class ShiftFloatNode(ShiftFilterNode):
    """Filter node to represent a shift float filter."""

    nodeName = "filter_shift_float"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT)


class ShiftColorNode(ShiftFilterNode):
    """Filter node to represent a shift color filter."""

    nodeName = "filter_shift_color"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR)


class AutoTrackerNode(FilterNode):
    """Filter node to represent an auto-tracker filter."""

    nodeName = "AutoTracker"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.VFILTER_AUTOTRACKER,
            name=name,
            allow_add_output=True,
        )


class EffectsStackNode(FilterNode):
    """Filter node to represent an effects stack filter."""

    nodeName = "EffectsStack"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.VFILTER_EFFECTSSTACK,
            name=name,
            allow_add_output=True,
        )


class SequencerNode(FilterNode):
    """Filternode to represent a sequencer filter."""

    nodeName = "Sequencer"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.VFILTER_SEQUENCER,
            name=name,
            allow_add_output=True,
        )

class ChaserNode(FilterNode):
    """Filter node for color chaser filter."""

    nodeName = "chase_filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.FILTER_COLOR_CHASER,
            name = name,
            terminals={"time": {"io": "in"}, "time_scale": {"io": "in"}},
            allow_add_input=True,
            allow_add_output=True
        )

        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.in_data_types["time_scale"] = DataType.DT_DOUBLE
        self.filter.default_values["time_scale"] = "1.0"

        if self.filter.filter_configurations.get("number_of_pixels") is None:
            self.filter.filter_configurations["number_of_pixels"] = "1"

        if self.filter.filter_configurations.get("color_parameters") is None:
            self.filter.filter_configurations["color_parameters"] = ""

        if self.filter.filter_configurations.get("number_parameters") is None:
            self.filter.filter_configurations["number_parameters"] = ""

        if self.filter.filter_configurations.get("presets") is None:
            self.filter.filter_configurations["presets"] = ""

        if self.filter.filter_configurations.get("trigger_event") is None:
            self.filter.filter_configurations["trigger_event"] = ""

        if self.filter.initial_parameters.get("config") is None:
            self.filter.initial_parameters["config"] = ""

        self._update_ports()

    @override
    def update_node_after_settings_changed(self) -> None:
        self._update_ports()

    def _update_ports(self) -> None:
        required_number_inputs = self.filter.filter_configurations["number_parameters"]
        required_number_inputs = set(required_number_inputs.split(":")) if len(required_number_inputs) > 0 else set()
        required_color_inputs = self.filter.filter_configurations["color_parameters"]
        required_color_inputs = set(required_color_inputs.split(":")) if len(required_color_inputs) > 0 else set()

        existing_inputs = set(self.inputs())
        for input_to_remove in existing_inputs - (
                required_number_inputs | required_color_inputs | {"time", "time_scale"}):
            self.removeTerminal(input_to_remove)

        for number_input in required_number_inputs:
            if number_input not in existing_inputs:
                self.addInput(number_input)
                self.filter.in_data_types[number_input] = DataType.DT_16_BIT
                self.filter.default_values[number_input] = "0"

        for color_input in required_color_inputs:
            if color_input not in existing_inputs:
                self.addInput(color_input)
                self.filter.in_data_types[color_input] = DataType.DT_COLOR
                self.filter.default_values[color_input] = "360.0,1.0,1.0"

        required_outputs = {str(i) for i in range(int(self.filter.filter_configurations["number_of_pixels"]))}
        existing_outputs = set(self.outputs())
        for output_to_remove in existing_outputs - required_outputs:
            self.removeTerminal(output_to_remove)

        for output_to_add in required_outputs - existing_outputs:
            self.addOutput(output_to_add)
            self.filter.out_data_types[output_to_add] = DataType.DT_COLOR
