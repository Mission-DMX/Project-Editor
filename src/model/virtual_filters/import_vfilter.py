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

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None) -> None:
        """Initialize the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_IMPORT, pos=pos)

    @override
    def _rebuild_io(self) -> None:
        """Mirror the referenced target filter's outputs after applying the rename mapping.

        At construction time the target is usually not yet patched in; the lookup silently
        leaves ``out_data_types`` empty and gets re-run later via
        :meth:`model.filter.Filter.update_filter_configuration` (and the loader's
        post-population ``_rebuild_io`` call) once the target id is known.
        """
        self._in_data_types = {}
        self._out_data_types = {}
        self._default_values = {}
        self._gui_update_keys = {}
        self._filter_configurations.setdefault("target", "")
        self._filter_configurations.setdefault("rename_dict", "")
        target_filter_id = self._filter_configurations.get("target", "")
        if not target_filter_id:
            return
        if self._scene is None:
            return
        target_filter = self._scene.get_filter_by_id(target_filter_id)
        if not isinstance(target_filter, Filter):
            return
        rename_dict: dict[str, str] = {}
        for entry in self._filter_configurations.get("rename_dict", "").split(","):
            if "=" not in entry:
                continue
            k, v = entry.split("=")
            rename_dict[k] = v
        for port_name, port_dt in target_filter.out_data_types.items():
            new_name = rename_dict.get(port_name, port_name)
            if new_name == "":
                # Explicit mapping to empty string hides the port.
                continue
            self._out_data_types[new_name] = port_dt

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
        """No native filter needed; outputs forward to the resolved target port."""
