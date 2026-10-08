"""Filter import node."""
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class ImportNode(FilterNode):
    """Filter node for importing filters from another show file."""

    nodeName = "Filter Import"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(
            model=model, filter_type=FilterTypeEnumeration.VFILTER_IMPORT, name=name, allow_add_output=True,
        )
