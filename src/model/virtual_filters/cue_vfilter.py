"""This file contains the switching vFilter implementation for the cue filter."""
from logging import getLogger
from typing import TYPE_CHECKING

from model import Filter, Scene
from model.filter import DataType, FilterTypeEnumeration, VirtualFilter

if TYPE_CHECKING:
    from view.show_mode.editor.node_editor_widgets import CueEditor
    from view.show_mode.show_ui_widgets import CueControlUIWidget

logger = getLogger(__file__)


class CueFilter(VirtualFilter):
    """
    This class implements a switch for the cue filter. In case of enabled live preview it links the faders of the
    temporary bank set to the outputs of the filter. Otherwise, it will simply instantiate a plain cue filter on
    elaboration.
    """

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, filter_type=int(FilterTypeEnumeration.VFILTER_CUES), pos=pos)
        self.in_preview_mode = False
        self.associated_editor_widget: CueEditor | None = None
        self._channel_mapping: dict[str, str] = {}
        self.linked_ui_widgets: list[CueControlUIWidget] = []

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        if self.in_preview_mode:
            # query the corresponding output channels from the fader filters
            return self._channel_mapping.get(virtual_port_id)

        # just return the output ports as-is
        return f"{self.filter_id}:{virtual_port_id}"

    def instantiate_filters(self, filter_list: list[Filter]):
        if self.in_preview_mode:
            if self.associated_editor_widget is None:
                raise RuntimeError("The preview mode has been enabled but no editor was assigned. This is a bug.")
            for channel in self.associated_editor_widget.channels:
                fader_filter_id = f"{self.filter_id}__{channel.name}"
                if channel.fader is None:
                    logger.error(
                        "The preview is enabled but no logger was assigned for channel '%s'.", channel.name)
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

                fader_filter.filter_configurations["column_id"] = channel.fader.id
                fader_filter.filter_configurations["set_id"] = channel.bankset.id
                fader_filter.filter_configurations["ignore_main_brightness_control"] = "true"

                if channel.data_type == DataType.DT_8_BIT:
                    adapter_filter_name = f"{self.filter_id}__ADAPTER__{channel.name}"
                    adapter_filter = Filter(self.scene, adapter_filter_name,
                                            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT,
                                            pos=self.pos)
                    adapter_filter.channel_links["value"] = fader_filter_id
                    fader_filter_id = adapter_filter_name + ":value_upper"
                    filter_list.append(adapter_filter)
                elif channel.data_type in [DataType.DT_BOOL, DataType.DT_DOUBLE]:
                    adapter_filter_name = f"{self.filter_id}__ADAPTER__{channel.name}"
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
            f.in_data_types.update(self.in_data_types)
            f.default_values.update(self.default_values)
            filter_list.append(f)
