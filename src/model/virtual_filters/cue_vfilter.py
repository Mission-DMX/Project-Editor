from model import Filter, Scene
from model.filter import VirtualFilter, FilterTypeEnumeration
from view.show_mode.editor.node_editor_widgets import CueEditor


class CueFilter(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, filter_type=int(FilterTypeEnumeration.VFILTER_CUES), pos=pos)
        self.in_preview_mode = False
        self.associated_editor_widget: CueEditor | None = None

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        # TODO implement
        pass

    def instantiate_filters(self, filter_list: list[Filter]):
        if self.in_preview_mode:
            if self.associated_editor_widget is None:
                raise RuntimeError("The preview mode has been enabled but no editor was assigned. This is a bug.")
            # TODO implement
            pass
        else:
            f = Filter(self.scene, self.filter_id, FilterTypeEnumeration.FILTER_TYPE_CUES, self.pos)
            f.filter_configurations.update(self.filter_configurations)
            f.channel_links.update(self.channel_links)
            f.gui_update_keys.update(self.gui_update_keys)
            f.initial_parameters.update(self.initial_parameters)
            filter_list.append(f)
