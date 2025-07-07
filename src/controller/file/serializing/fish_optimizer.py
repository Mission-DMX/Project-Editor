import logging
from xml.etree import ElementTree

from model import Filter
from model.filter import DataType, FilterTypeEnumeration

logger = logging.Logger(__file__)


class SceneOptimizerModule:
    """
    This class contains information required for performing post-processing on a single scene.
    """

    def __init__(self, replacing_enabled: bool):
        self._replacing_enabled = replacing_enabled
        self.channel_override_dict: dict[str, str] = {}
        self.channel_link_list: list[tuple[Filter, ElementTree.SubElement]] = []
        self._global_time_input_filter: Filter | None = None
        self._main_brightness_input_filter: Filter | None = None
        self._universe_filter_dict: dict[str, list[tuple[str, str, str]]] = {}
        self._first_universe_filter_id: dict[str, str] = {}

    def _substitute_universe_filter(self, f: Filter):
        """
        This method reads the filter configuration and updates the universe filter creation dict.
        Entries are lists of tuple (input_channel_name, corresponding_universe_channel, foreign_output_channel_to_map).

        :param f: The universe filter to read.
        """
        universe_id = f.filter_configurations['universe']
        fde = self._universe_filter_dict.get(universe_id)
        if not fde:
            fde = []
            self._universe_filter_dict[universe_id] = fde
        for k, v in f.filter_configurations.items():
            if k == 'universe':
                continue
            fde.append((str(f.filter_id) + "__" + str(k), v, str(f.channel_links.get(k))))
        self._first_universe_filter_id[universe_id] = f.filter_id

    def filter_was_substituted(self, f: Filter) -> bool:
        """
        This method receives a filter and checks if it can be substituted with an equivalent filter that was already
        placed. If this turns out to be the case, this method fills the output port substitution dictionary with
        information for the given filter. Otherwise, false will be returned.

        :param f: The filter to check for substitution.
        :returns: true if the filter was scheduled to be substituted
        and therefore should not be emplaced for transmission to fish.
        """
        match f.filter_type:
            # TODO expand this by also reduce constants with the same value
            case FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT:
                if len(f.out_data_types) == 0:
                    f.out_data_types["value"] = DataType.DT_DOUBLE
                if self._global_time_input_filter is not None:
                    self._fill_ch_sub_dict(f, self._global_time_input_filter)
                    # logger.debug("Substituting time filter {}.".format(f.filter_id))
                    return True

                self._global_time_input_filter = f
                return False
            case FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS:
                if len(f.out_data_types) == 0:
                    f.out_data_types["brightness"] = DataType.DT_16_BIT
                if self._main_brightness_input_filter is not None:
                    self._fill_ch_sub_dict(f, self._main_brightness_input_filter)
                    return True

                self._main_brightness_input_filter = f
                return False
            case FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT:
                self._substitute_universe_filter(f)
                return True
            case _:
                return False

    def _fill_ch_sub_dict(self, f: Filter, substitution_filter: Filter):
        """
        This method is used to fill the substitution dictionary with required port mappings.

        :param f: The filter that should be substituted
        :param substitution_filter: The filter that was already emplaced and should be used as a substitution.
        """
        if f.filter_type != substitution_filter.filter_type:
            raise ValueError("Cannot substitute two filters of different type.")
        if f.is_virtual_filter:
            raise ValueError("Cannot substitute virtual filters.")
        if f.scene != substitution_filter.scene:
            raise ValueError("Cannot substitute a filter with one from another scene.")
        logger.debug(
            "Substituted filter %s with %s in scene %s.", f.filter_id, substitution_filter.filter_id,
            f.scene.scene_id)
        for output_channel_name in f.out_data_types:
            self.channel_override_dict[
                f"{f.filter_id}:{output_channel_name}"] = f"{substitution_filter.filter_id}:{output_channel_name}"

    def _emplace_universe_filters(self, scene_element: ElementTree.Element):
        """
        This method places the replacement for the aggregated universe output filters.
        :param scene_element: The scene to place the new filter into.
        """
        for universe, channel_list in self._universe_filter_dict.items():
            filter_config_parameters = {'universe': universe}
            channel_mappings = {}
            for channel_mapping in channel_list:
                filter_input_channel, universe_channel, foreign_filter_output_channel = channel_mapping
                filter_config_parameters[filter_input_channel] = str(int(universe_channel) - 1)
                if foreign_filter_output_channel in self.channel_override_dict:
                    foreign_filter_output_channel = self.channel_override_dict.get(foreign_filter_output_channel)
                channel_mappings[filter_input_channel] = foreign_filter_output_channel
            filter_element = ElementTree.SubElement(scene_element, "filter", attrib={
                "id": str(self._first_universe_filter_id[universe]),
                "type": str(FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT),
                "pos": "0,0"
            })
            for param_k, param_v in filter_config_parameters.items():
                ElementTree.SubElement(filter_element, "filterConfiguration", {
                    'name': str(param_k),
                    'value': str(param_v)
                })
            for input_ch, output_ch in channel_mappings.items():
                ElementTree.SubElement(filter_element, "channellink", attrib={
                    "input_channel_id": str(input_ch),
                    "output_channel_id": str(output_ch)
                })

    def wrap_up(self, scene_element: ElementTree.Element):
        """This method needs to be called in order to apply the optimization steps that have been staged.
        :param scene_element: The scene XML element to write to."""
        self._emplace_universe_filters(scene_element)
