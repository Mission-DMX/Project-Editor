"""Debug filter nodes."""
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class DebugNode(FilterNode):
    """Basic debug node."""

    def __init__(self, model: Filter, name: str, filter_type: int) -> None:
        """Initialize filter node."""
        super().__init__(model, filter_type, name)


class Debug8BitNode(DebugNode):
    """Filter to debug an 8 bit value.

    TODO implement visualization.
    """

    nodeName = "8 Bit Filter (Debug)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_8BIT, name=name)


class Debug16BitNode(DebugNode):
    """Filter to debug a 16 bit value.

    TODO implement visualization.
    """

    nodeName = "16 Bit Filter (Debug)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_16BIT, name=name)


class DebugFloatNode(DebugNode):
    """Filter to debug a float/double value.

    TODO implement visualization.
    """

    nodeName = "Float Filter (Debug)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_FLOAT, name=name)


class DebugColorNode(DebugNode):
    """Filter to debug a color value.

    TODO implement visualization.
    """

    nodeName = "Color Filter (Debug)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_COLOR, name=name)


class DebugRemote8BitNode(DebugNode):
    """Filter to debug an 8 bit value.

    TODO implement visualization.
    """

    nodeName = "8 Bit Filter (Debug, Remote)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT, name=name)


class DebugRemote16BitNode(DebugNode):
    """Filter to debug a 16 bit value.

    TODO implement visualization.
    """

    nodeName = "16 Bit Filter (Debug, Remote)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT, name=name)


class DebugRemoteFloatNode(DebugNode):
    """Filter to debug a float/double value.

    TODO implement visualization.
    """

    nodeName = "Float Filter (Debug, Remote)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_FLOAT, name=name)


class DebugRemoteColorNode(DebugNode):
    """Filter to debug a color value.

    TODO implement visualization.
    """

    nodeName = "Color Filter (Debug, Remote)"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_PIXEL, name=name)
