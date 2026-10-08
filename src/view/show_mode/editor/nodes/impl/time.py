"""Filter nodes related to time."""

from model import Scene
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class TimeNode(FilterNode):
    """Filter to represent time."""

    nodeName = "Time"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT, name=name)
        self.channel_hints["value"] = " [ms]"


class EventCounterFilterNode(FilterNode):
    """Filter to count events."""

    nodeName = "Event Counter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_EVENT_COUNTER, name=name)
        self.channel_hints["time"] = " [ms]"


class TimeSwitchOnDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time on-switch."""

    nodeName = "Switch on delay - 8 bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_8BIT, name=name)


class TimeSwitchOnDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time on-switch."""

    nodeName = "Switch on delay - 16 bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_16BIT, name=name)


class TimeSwitchOnDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time on-switch."""

    nodeName = "Switch on delay - float"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_FLOAT, name=name)


class TimeSwitchOffDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time off-switch."""

    nodeName = "Switch off delay - 8 bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_8BIT, name=name)


class TimeSwitchOffDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time off-switch."""

    nodeName = "Switch off delay - 16 bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_16BIT, name=name)


class TimeSwitchOffDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time off-switch."""

    nodeName = "Switch off delay - float"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_FLOAT, name=name)
