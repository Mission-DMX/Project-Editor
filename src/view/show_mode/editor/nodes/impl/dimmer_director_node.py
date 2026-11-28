"""Node graph object for the Dimmer Director filter (type 84)."""

from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes import FilterNode


class DimmerDirectorNode(FilterNode):
    """Filter node wrapping ``DimmerDirectorFilter``."""

    nodeName = "Dimmer Director"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize the dimmer director filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_DIMMER_DIRECTOR, name=name)
