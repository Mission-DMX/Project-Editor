from model import Filter
from model.filter import VirtualFilter


class AutoTrackerFilter(VirtualFilter):
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
