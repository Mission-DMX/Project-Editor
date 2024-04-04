from model import Filter
from model.filter import VirtualFilter, FilterTypeEnumeration


class CueFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, filter_type: int, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, filter_type, pos)
        self.in_preview_mode = False

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        # TODO implement
        pass

    def instantiate_filters(self, filter_list: list[Filter]):
        if self.in_preview_mode:
            # TODO implement
            pass
        else:
            f = Filter(self.scene, self.filter_id, FilterTypeEnumeration.FILTER_TYPE_CUES, self.pos)
            f.filter_configurations.update(self.filter_configurations)
            f.channel_links.update(self.channel_links)
            f.gui_update_keys.update(self.gui_update_keys)
            f.initial_parameters.update(self.initial_parameters)
            filter_list.append(f)
