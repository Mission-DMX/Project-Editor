from model import Filter, Scene
from model.filter import VirtualFilter, FilterTypeEnumeration, DataType
from view.show_mode.editor.node_editor_widgets import CueEditor


from logging import getLogger
logger = getLogger(__file__)


class CueFilter(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, filter_type=int(FilterTypeEnumeration.VFILTER_CUES), pos=pos)
        self.in_preview_mode = False
        self.associated_editor_widget: CueEditor | None = None
        self._channel_mapping: dict[str, str] = {}

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        if self.in_preview_mode:
            return self._channel_mapping.get(virtual_port_id)
        else:
            return "{}:{}".format(self.filter_id, virtual_port_id)

    def instantiate_filters(self, filter_list: list[Filter]):
        if self.in_preview_mode:
            if self.associated_editor_widget is None:
                raise RuntimeError("The preview mode has been enabled but no editor was assigned. This is a bug.")
            for channel in self.associated_editor_widget.channels:
                fader_filter_id = "{}__{}".format(self.filter_id, channel.name)
                if channel.fader is None:
                    logger.error("The preview is enabled but no logger was assigned for channel '{}'.".format(channel.name))
                    fader_filter = Filter(self.scene, fader_filter_id,
                                          filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR
                                          if channel.data_type == DataType.DT_COLOR
                                          else FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, pos=self.pos)
                    fader_filter_id += ":value"
                else:
                    fader_filter = Filter(self.scene, fader_filter_id,
                                          filter_type=FilterTypeEnumeration.FILTER_FADER_HSI if
                                          channel.data_type == DataType.DT_COLOR else
                                          FilterTypeEnumeration.FILTER_FADER_RAW,
                                          pos=self.pos)
                    fader_filter_id += ":color" if channel.data_type == DataType.DT_COLOR else ":primary"
                if channel.data_type == DataType.DT_8_BIT:
                    adapter_filter_name = "{}__ADAPTER__{}".format(self.filter_id, channel.name)
                    adapter_filter = Filter(self.scene, adapter_filter_name,
                                            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT,
                                            pos=self.pos)
                    adapter_filter.channel_links["value"] = fader_filter_id
                    fader_filter_id = adapter_filter_name + ":value_upper"
                    filter_list.append(adapter_filter)
                elif channel.data_type in [DataType.DT_BOOL, DataType.DT_DOUBLE]:
                    adapter_filter_name = "{}__ADAPTER__{}".format(self.filter_id, channel.name)
                    adapter_filter = Filter(self.scene, adapter_filter_name,
                                            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL
                                            if channel.data_type == DataType.DT_BOOL else
                                            FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT,
                                            pos=self.pos)
                    adapter_filter.channel_links["value_in"] = fader_filter_id
                    fader_filter_id = adapter_filter_name + ":value"
                    filter_list.append(adapter_filter)
                self._channel_mapping[channel.name] = fader_filter_id
                filter_list.append(fader_filter)
        else:
            f = Filter(self.scene, self.filter_id, FilterTypeEnumeration.FILTER_TYPE_CUES, self.pos)
            f.filter_configurations.update(self.filter_configurations)
            f.channel_links.update(self.channel_links)
            f.gui_update_keys.update(self.gui_update_keys)
            f.initial_parameters.update(self.initial_parameters)
            filter_list.append(f)
