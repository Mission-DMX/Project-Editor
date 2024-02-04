import logging
from xml.etree import ElementTree

from model import Filter
from model.filter import FilterTypeEnumeration

logger = logging.Logger(__file__)


class SceneOptimizerModule:
    """
    This class contains information required for performing post-processing on a single scene.
    """

    def __init__(self):
        self.channel_override_dict: dict[str, str] = dict()
        self.channel_link_list: list[tuple[Filter, ElementTree.SubElement]] = []
        self._global_time_input_filter: Filter | None = None
        self._main_brightness_input_filter: Filter | None = None
        self._universe_filter_dict: dict[str, list[tuple[str]]] = dict()

    def _substitute_universe_filter(self, f: Filter):
        """
        This method reads the filter configuration and updates the universe filter creation dict.
        Entries are lists of tuple (input_channel_name, corresponding_universe_channel, foreign_output_channel_to_map).

        :param f: The universe filter to read.
        """
        universe_id = f.filter_configuration['universe']
        fde = self._universe_filter_dict.get(universe_id)
        if not fde:
            fde = []
            self._universe_filter_dict[universe_id] = fde
        for k, v in f.filter_configuration.items():
            if k == 'universe':
                continue
            fde.append(tuple([k, v, str(f.channel_links.get(k))]))
        pass

    def filter_was_substituted(self, f: Filter) -> bool:
        """
        This method receives a filter and checks if it can be substituted with an equivalent filter that was already
        placed. If this turns out to be the case, this method fills the output port substitution dictionary with
        information for the given filter. Otherwise, false will be returned.

        :param f: The filter to check for substitution.
        :returns: true if the filter was scheduled to be substituted and therefore should not be emplaced for transmission to fish.
        """
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
            case FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT:
                self._substitute_universe_filter(f)
                return False  # FIXME replace me with True once universe filter output has been implemented
            case _:
                return False

    # TODO write function to place universe outputs

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
        logger.debug("Substituted filter {} with {} in scene {}.".format(
            f.filter_id, substitution_filter.filter_id, f.scene.scene_id))
        for output_channel_name in f.out_data_types.keys():
            self.channel_override_dict["{}:{}".format(f.filter_id, output_channel_name)] = "{}:{}".format(
                substitution_filter.filter_id, output_channel_name)
