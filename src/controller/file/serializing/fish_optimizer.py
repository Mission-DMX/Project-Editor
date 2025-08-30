"""Post processing helper."""

import xml.etree.ElementTree as ET
from logging import getLogger

from model import Filter
from model.filter import DataType, FilterTypeEnumeration

logger = getLogger(__name__)


class SceneOptimizerModule:
    """Post-processing helper for a single scene.

    This class collects information during scene construction and
    applies optimizations such as filter substitution or aggregation
    of universe filters.
    """

    def __init__(self, replacing_enabled: bool) -> None:
        """Initialize the scene optimizer.

        Args:
            replacing_enabled: Whether substitution of filters is allowed.

        """
        self._replacing_enabled = replacing_enabled
        self.channel_override_dict: dict[str, str] = {}
        self.channel_link_list: list[tuple[Filter, ET.SubElement]] = []
        self._global_time_input_filter: Filter | None = None
        self._main_brightness_input_filter: Filter | None = None
        self._universe_filter_dict: dict[str, list[tuple[str, str, str]]] = {}
        self._first_universe_filter_id: dict[str, str] = {}

    def _substitute_universe_filter(self, f: Filter) -> None:
        """Register a universe filter for later aggregation.

        Updates the internal dictionary of universe filters with the given filters configuration.
        Each entry is a tuple of ``(input_channel_name, universe_channel, foreign_output_channel)``.

        Args:
            f: The universe filter to register.

        """
        universe_id = f.filter_configurations["universe"]
        fde = self._universe_filter_dict.get(universe_id)
        if not fde:
            fde = []
            self._universe_filter_dict[universe_id] = fde
        for k, v in f.filter_configurations.items():
            if k == "universe":
                continue
            fde.append((f"{f.filter_id}__{k}", v, str(f.channel_links.get(k))))
        self._first_universe_filter_id[universe_id] = f.filter_id

    def filter_was_substituted(self, f: Filter) -> bool:
        """Check whether a filter can be substituted.

        If the filter can be replaced by an equivalent filter already present in the scene, the substitution dictionary
        is updated and ``True`` is returned. Otherwise, the filter is kept.

        Args:
            f: The filter to check.

        Returns:
            True if the filter was substituted and should not be placed again. False otherwise.

        """
        match f.filter_type:
            # TODO expand this by also reduce constants with the same value
            case FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT:
                if len(f.out_data_types) == 0:
                    f.out_data_types["value"] = DataType.DT_DOUBLE
                if self._global_time_input_filter is not None:
                    self._fill_ch_sub_dict(f, self._global_time_input_filter)
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

    def _fill_ch_sub_dict(self, f: Filter, substitution_filter: Filter) -> None:
        """Populate the substitution dictionary with channel mappings.

        Args:
            f: The filter to be substituted.
            substitution_filter: The filter that replaces ``f``.

        Raises:
            ValueError: If the filters are of different type, virtual, or belong to different scenes.

        """
        if f.filter_type != substitution_filter.filter_type:
            raise ValueError("Cannot substitute two filters of different type.")
        if f.is_virtual_filter:
            raise ValueError("Cannot substitute virtual filters.")
        if f.scene != substitution_filter.scene:
            raise ValueError("Cannot substitute a filter with one from another scene.")
        logger.debug(
            "Substituted filter %s with %s in scene %s.", f.filter_id, substitution_filter.filter_id, f.scene.scene_id
        )
        for output_channel_name in f.out_data_types:
            self.channel_override_dict[f"{f.filter_id}:{output_channel_name}"] = (
                f"{substitution_filter.filter_id}:{output_channel_name}"
            )

    def _emplace_universe_filters(self, scene_element: ET.Element) -> None:
        """Insert aggregated universe filters into the scene XML.

        Args:
            scene_element: The XML element representing the scene.

        """
        for universe, channel_list in self._universe_filter_dict.items():
            filter_config_parameters = {"universe": universe}
            channel_mappings = {}
            for channel_mapping in channel_list:
                filter_input_channel, universe_channel, foreign_filter_output_channel = channel_mapping
                filter_config_parameters[filter_input_channel] = str(int(universe_channel) - 1)
                if foreign_filter_output_channel in self.channel_override_dict:
                    foreign_filter_output_channel = self.channel_override_dict.get(foreign_filter_output_channel)
                channel_mappings[filter_input_channel] = foreign_filter_output_channel
            filter_element = ET.SubElement(
                scene_element,
                "filter",
                attrib={
                    "id": str(self._first_universe_filter_id[universe]),
                    "type": str(FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT),
                    "pos": "0,0",
                },
            )
            for param_k, param_v in filter_config_parameters.items():
                ET.SubElement(
                    filter_element,
                    "filterConfiguration",
                    {
                        "name": str(param_k),
                        "value": str(param_v),
                    },
                )
            for input_ch, output_ch in channel_mappings.items():
                ET.SubElement(
                    filter_element,
                    "channellink",
                    attrib={
                        "input_channel_id": str(input_ch),
                        "output_channel_id": str(output_ch),
                    },
                )

    def wrap_up(self, scene_element: ET.Element) -> None:
        """Finalize and apply staged optimizations.

        This method must be called once all filters have been processed
        in order to write the aggregated results into the scene.

        Args:
            scene_element: The XML element representing the scene.

        """
        self._emplace_universe_filters(scene_element)
