"""Contains filter nodes for signal routing filters."""

from __future__ import annotations

from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class SwitchFilterNode(FilterNode):
    """Base class to represent abstract switch filter."""

    def __init__(self, model: Filter, name: str, filter_type: int) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=filter_type, name=name, allow_add_output=True)


class Switch8BitNode(SwitchFilterNode):
    """8 bit switch filter node implementation."""

    nodeName = "filter_switch_8bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_8BIT)


class Switch16BitNode(SwitchFilterNode):
    """16 bit switch filter node implementation."""

    nodeName = "filter_switch_16bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_16BIT)


class SwitchFloatNode(SwitchFilterNode):
    """Float switch filter node implementation."""

    nodeName = "filter_switch_float"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_FLOAT)


class SwitchColorNode(SwitchFilterNode):
    """8 bit switch filter node implementation."""

    nodeName = "filter_switch_color"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model, name, FilterTypeEnumeration.FILTER_SWITCH_COLOR)
