"""Scripting filter nodes."""
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class LuaFilterNode(FilterNode):
    """Lua scripting filter node. I/O channels come from the filter's mapping configurations."""

    nodeName = "Lua"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize the Lua filter node.

        The pyqtgraph ``allow_add_output`` flag keeps the built-in "+" affordance for
        interactive output addition; terminals themselves are derived from the model filter's
        I/O signature by the base class.
        """
        super().__init__(
            model=model, filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA, name=name, allow_add_output=True
        )
