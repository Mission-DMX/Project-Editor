from model import Filter, Scene
from model.filter import FilterTypeEnumeration, VirtualFilter


class ImportVFilter(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_IMPORT, pos=pos)
        if "target" not in self.filter_configurations:
            self.filter_configurations["target"] = ""
        if "rename_dict" not in self.filter_configurations:
            self.filter_configurations["rename_dict"] = ""

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
        return f"{target_filter_id}:{virtual_port_id}"

    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        # Nothing to do here as were simply forwarding the filter.
        pass
