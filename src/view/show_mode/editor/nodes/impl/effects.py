"""Filter Nodes for effect filters."""

from model import Scene
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
            name=name,
            allow_add_input=True,
            allow_add_output=True,
        )
