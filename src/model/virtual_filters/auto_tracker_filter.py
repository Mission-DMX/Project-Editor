from model import Filter, Scene
from model.filter import VirtualFilter, FilterTypeEnumeration


class AutoTrackerFilter(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_AUTOTRACKER, pos=pos)

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        pass

    def instantiate_filters(self, filter_list: list[Filter]):
        pass

    @property
    def number_of_concurrent_trackers(self) -> int:
        tr = self.filter_configurations.get("trackercount")
        if tr:
            try:
                tr = int(tr)
                if tr >= 0:
                    return tr
            except ValueError:
                pass
        self.filter_configurations['trackercount'] = '0'
        return 0
