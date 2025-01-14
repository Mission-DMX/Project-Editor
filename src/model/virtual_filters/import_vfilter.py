from model import Filter
from model.filter import VirtualFilter, FilterTypeEnumeration


class ImportVFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_IMPORT, pos=pos)
        if "target" not in self.filter_configurations.keys():
            self.filter_configurations["target"] = ""

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        target_filter_id = self.filter_configurations.get("target")
        if target_filter_id is None or target_filter_id == "":
            return None
        return "{}:{}".format(target_filter_id, virtual_port_id)

    def instantiate_filters(self, filter_list: list[Filter]):
        # Nothing to do here as were simply forwarding the filter.
        pass
