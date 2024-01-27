import logging
from xml.etree import ElementTree

from model import Filter
from model.filter import FilterTypeEnumeration

logger = logging.Logger(__file__)


class SceneOptimizerModule:
    def __init__(self):
        self.channel_override_dict: dict[str, str] = dict()
        self.channel_link_list: list[tuple[Filter, ElementTree.SubElement]] = []
        self._global_time_input_filter: Filter | None = None
        self._main_brightness_input_filter: Filter | None = None

    def filter_was_substituted(self, f: Filter):
        match f.filter_type:
            case FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT:
                if self._global_time_input_filter is not None:
                    self._fill_ch_sub_dict(f, self._global_time_input_filter)
                    return True
                else:
                    self._global_time_input_filter = f
                    return False
            case FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS:
                if self._main_brightness_input_filter is not None:
                    self._fill_ch_sub_dict(f, self._main_brightness_input_filter)
                    return True
                else:
                    self._main_brightness_input_filter = f
                    return False
            case _:
                return False

    def _fill_ch_sub_dict(self, f: Filter, substitution_filter: Filter):
        if f.filter_type != substitution_filter.filter_type:
            raise ValueError("Cannot substitute two filters of different type.")
        if f.is_virtual_filter:
            raise ValueError("Cannot substitute virtual filters.")
        if f.scene != substitution_filter.scene:
            raise ValueError("Cannot substitute a filter with one from another scene.")
        logger.debug("Substituted filter {} with {} in scene {}.".format(
            f.filter_id, substitution_filter.filter_id, f.scene.scene_id))
        for output_channel_name in f.out_data_types.keys():
            self.channel_override_dict["{}:{}".format(f.filter_id, output_channel_name)] = "{}:{}".format(
                substitution_filter.filter_id, output_channel_name)
