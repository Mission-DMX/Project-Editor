from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class ImportNode(FilterNode):
    nodeName = "Filter Import"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(
            model=model, filter_type=FilterTypeEnumeration.VFILTER_IMPORT, name=name, allow_add_output=True,
        )
