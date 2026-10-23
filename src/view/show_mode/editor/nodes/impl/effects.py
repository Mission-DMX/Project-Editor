"""Filter Nodes for effect filters."""

from model import Scene
from model.filter import DataType, Filter, FilterTypeEnumeration
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


class PropertyBasedCuesNode(FilterNode):
    """Filter node to represent the property-based cue vfilter."""

    nodeName = "Property Cues"  # noqa: N815 nodeName Required for FilterNode

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES,
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
            name=name,
            allow_add_input=True,
            allow_add_output=True,
        )


class _StrobeGeneratorBase(FilterNode):
    """Shared setup for the series strobe generator filter nodes."""

    _BRIGHTNESS_DT: DataType = DataType.DT_DOUBLE

    def __init__(self, model: Filter, name: str, filter_type: int) -> None:
        """Initialize strobe generator filter node."""
        super().__init__(model=model, filter_type=filter_type, name=name)
        brightness_dt = type(self)._BRIGHTNESS_DT
        for in_name in ("brightness", "frequency", "duty_cycle"):
            if in_name not in self.inputs():
                self.addInput(in_name)
        if "value" not in self.outputs():
            self.addOutput("value")
        self.filter.in_data_types["brightness"] = brightness_dt
        self.filter.in_data_types["frequency"] = DataType.DT_8_BIT
        self.filter.in_data_types["duty_cycle"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = brightness_dt
        self.filter.default_values.setdefault("brightness", "0")
        self.filter.default_values.setdefault("frequency", "0")
        self.filter.default_values.setdefault("duty_cycle", "128")
        self.filter.filter_configurations.setdefault("slowest_period_ms", "500.0")


class StrobeGenerator8BitNode(_StrobeGeneratorBase):
    """Filter node for the 8-bit series strobe generator."""

    nodeName = "Strobe Generator (8bit)"  # noqa: N815
    _BRIGHTNESS_DT: DataType = DataType.DT_8_BIT

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_8BIT)


class StrobeGenerator16BitNode(_StrobeGeneratorBase):
    """Filter node for the 16-bit series strobe generator."""

    nodeName = "Strobe Generator (16bit)"  # noqa: N815
    _BRIGHTNESS_DT: DataType = DataType.DT_16_BIT

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_16BIT)


class StrobeGeneratorFloatNode(_StrobeGeneratorBase):
    """Filter node for the float series strobe generator."""

    nodeName = "Strobe Generator (float)"  # noqa: N815
    _BRIGHTNESS_DT: DataType = DataType.DT_DOUBLE

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
