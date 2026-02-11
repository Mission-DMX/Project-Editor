"""Virtual Filter for importing filters from other filter pages."""
from logging import getLogger
from typing import override

from model import Filter, Scene
from model.filter import FilterTypeEnumeration, VirtualFilter

logger = getLogger(__name__)


class ImportVFilter(VirtualFilter):
    """ImportVFilter.

    This virtual filter imports a filter from other filter pages.

    """

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Initialize the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_IMPORT, pos=pos)
        if "target" not in self.filter_configurations:
            self.filter_configurations["target"] = ""
        if "rename_dict" not in self.filter_configurations:
            self.filter_configurations["rename_dict"] = ""

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        target_filter_id = self.filter_configurations.get("target")
        if target_filter_id is None or target_filter_id == "":
            return None
        rename_data = self.filter_configurations.get("rename_dict")
        if rename_data is not None:
            for entry in rename_data.split(","):
                if "=" not in entry:
                    continue
                k, v = entry.split("=")
                if virtual_port_id == k:
                    if v == "":
                        return None
                    virtual_port_id = v
                    break
        filter_candidate = self.scene.get_filter_by_id(target_filter_id)
        if isinstance(filter_candidate, VirtualFilter):
            return filter_candidate.resolve_output_port_id(virtual_port_id)
        return f"{target_filter_id}:{virtual_port_id}"

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        # Nothing really to do here as were simply forwarding the filter. However, we need to make sure, that the
        # outputs exist.
        for item in self.filter_configurations["rename_dict"].split(","):
            if "=" not in item:
                logger.error("Invalid mapping '%s' in import filter config.", item)
                continue
            k, _ = item.split("=")
            if self.out_data_types.get(k) is None:
                self.out_data_types[k] = None  # We just need to make sure that init knows about them.
