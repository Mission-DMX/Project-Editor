# coding=utf-8
"""Filter module"""
import abc
from typing import TYPE_CHECKING
from enum import IntFlag, auto, Enum

if TYPE_CHECKING:
    from . import Scene


class DataType(IntFlag):
    """Data types used by filter channels"""
    DT_8_BIT = auto()
    DT_16_BIT = auto()
    DT_DOUBLE = auto()
    DT_COLOR = auto()
    DT_BOOL = auto()

    def format_for_filters(self):
        """This method returns the data type representation commonly used by the fish filters for configuration."""
        if self.value == DataType.DT_8_BIT.value:
            return "8bit"
        elif self.value == DataType.DT_16_BIT.value:
            return "16bit"
        elif self.value == DataType.DT_DOUBLE.value:
            return "float"
        elif self.value == DataType.DT_COLOR.value:
            return "color"
        else:
            return "8bit"  # bools are 8 bit

    @staticmethod
    def names() -> list[str]:
        return [f.format_for_filters() for f in [DataType.DT_8_BIT, DataType.DT_16_BIT, DataType.DT_DOUBLE,
                                                 DataType.DT_COLOR]]

    @staticmethod
    def from_filter_str(type_definition_string: str):
        match type_definition_string:
            case "8bit":
                return DataType.DT_8_BIT
            case "16bit":
                return DataType.DT_16_BIT
            case "float":
                return DataType.DT_DOUBLE
            case "color":
                return DataType.DT_COLOR
            case _:
                return DataType.DT_8_BIT

    def __str__(self) -> str:
        if self.value == DataType.DT_BOOL.value:
            return "bool (8bit)"
        return self.format_for_filters()


class FilterTypeEnumeration(IntFlag):
    VFILTER_COMBINED_FILTER_PRESET = -6
    VFILTER_POSITION_CONSTANT = -5
    VFILTER_EFFECTSSTACK = -4
    VFILTER_CUES = -3
    VFILTER_UNIVERSE = -2
    VFILTER_AUTOTRACKER = -1
    FILTER_CONSTANT_8BIT = 0
    FILTER_CONSTANT_16_BIT = 1
    FILTER_CONSTANT_FLOAT = 2
    FILTER_CONSTANT_COLOR = 3
    FILTER_DEBUG_OUTPUT_8BIT = 4
    FILTER_DEBUG_OUTPUT_16BIT = 5
    FILTER_DEBUG_OUTPUT_FLOAT = 6
    FILTER_DEBUG_OUTPUT_COLOR = 7
    FILTER_ADAPTER_16BIT_TO_DUAL_8BIT = 8
    FILTER_ADAPTER_16BIT_TO_BOOL = 9
    FILTER_ARITHMETICS_MAC = 10
    FILTER_UNIVERSE_OUTPUT = 11
    FILTER_ARITHMETICS_FLOAT_TO_16BIT = 12
    FILTER_ARITHMETICS_FLOAT_TO_8BIT = 13
    FILTER_ARITHMETICS_ROUND = 14
    FILTER_ADAPTER_COLOR_TO_RGB = 15
    FILTER_ADAPTER_COLOR_TO_RGBW = 16
    FILTER_ADAPTER_COLOR_TO_RGBWA = 17
    FILTER_ADAPTER_FLOAT_TO_COLOR = 18
    FILTER_ARITHMETICS_LOGARITHM = 28
    FILTER_ARITHMETICS_EXPONENTIAL = 29
    FILTER_ARITHMETICS_MINIMUM = 30
    FILTER_ARITHMETICS_MAXIMUM = 31
    FILTER_TYPE_TIME_INPUT = 32
    FILTER_FADER_RAW = 39
    FILTER_FADER_HSI = 40
    FILTER_FADER_HSIA = 41
    FILTER_FADER_HSIU = 42
    FILTER_FADER_HSIAU = 42
    FILTER_TYPE_CUES = 44
    FILTER_EFFECT_SHIFT_8BIT = 45
    FILTER_EFFECT_SHIFT_16BIT = 46
    FILTER_EFFECT_SHIFT_FLOAT = 47
    FILTER_EFFECT_SHIFT_COLOR = 48
    FILTER_TYPE_MAIN_BRIGHTNESS = 49
    FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT = 51
    FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT = 52
    FILTER_ADAPTER_COLOR_TO_FLOAT = 53
    FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE = 54
    FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE = 55
    FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE = 56
    FILTER_ADAPTER_DUAL_BYTE_TO_16BIT = 57
    FILTER_ADAPTER_8BIT_TO_16BIT = 58


class Filter:
    """Filter for show file"""

    def __init__(self, scene: "Scene", filter_id: str, filter_type: int, pos: tuple[int] | None = None):
        if pos is None:
            pos = [0.0, 0.0]
        self._scene: "Scene" = scene
        self._filter_id = filter_id
        self._filter_type = int(filter_type)
        self._pos: tuple[float, float] | None = pos
        self._channel_links: dict[str, str] = {}
        self._initial_parameters: dict[str, str] = {}
        self._filter_configurations: dict[str, str] = {}
        self._gui_update_keys: dict[str, DataType | list[str]] = {}
        self._in_data_types: dict[str, DataType] = {}
        self._out_data_types: dict[str, DataType] = {}

    @property
    def scene(self) -> "Scene":
        """The scene the filter belongs to"""
        return self._scene

    @property
    def filter_id(self) -> str:
        """The unique id/name of the filter. This is not to be confused with the filter type."""
        return self._filter_id

    @filter_id.setter
    def filter_id(self, id_):
        old_id: str = self._filter_id
        self._filter_id = id_
        if self.scene:
            self.scene.notify_about_filter_rename_action(self, old_id)

    @property
    def filter_type(self) -> int:
        """The type of the filter. This might be a positive number for a filter that fish understands or a negative
        one in case of a virtual filter that the GUI needs to resolve first."""
        return self._filter_type

    @property
    def pos(self) -> tuple[float] | None:
        """The position of the filter node inside the ui"""
        return self._pos

    @pos.setter
    def pos(self, pos: list[float, float]):
        self._pos = pos

    @property
    def channel_links(self) -> dict[str, str]:
        """Dict mapping the filters inputs to the connected outputs"""
        return self._channel_links

    @property
    def initial_parameters(self):
        """The initial parameters"""
        return self._initial_parameters

    @property
    def filter_configurations(self) -> dict[str, str]:
        """The filter configurations"""
        return self._filter_configurations

    @property
    def in_data_types(self) -> dict[str, DataType]:
        """Dict mapping input channel names to their data types."""
        return self._in_data_types

    @property
    def out_data_types(self) -> dict[str, DataType]:
        """Dict mapping output channel names to their data types"""
        return self._out_data_types

    @property
    def gui_update_keys(self) -> dict[str, DataType | str]:
        return self._gui_update_keys

    @property
    def is_virtual_filter(self) -> bool:
        return self.filter_type < 0

    def copy(self, new_scene: "Scene" = None, new_id: str = None) -> "Filter":
        f = Filter(new_scene if new_scene else self.scene, self._filter_id if not new_id else new_id, self._filter_type, self._pos)
        f._channel_links = self.channel_links.copy()
        f._initial_parameters = self._initial_parameters.copy()
        f._filter_configurations = self._filter_configurations.copy()
        f._in_data_types = self._in_data_types.copy()
        f._out_data_types = self._out_data_types.copy()
        f._gui_update_keys = self._gui_update_keys.copy()
        return f

    def __str__(self):
        return "Filter '{}' from scene '{}'".format(self._filter_id, self.scene)


class VirtualFilter(Filter, abc.ABC):
    """
    This abstract class can be used in order to implement virtual filters. The configuration of these filters is still
    stored within the filter configuration, however, these filters will not be sent to fish. Instead, their
    instantiate_filters method will be called in order to provide a representation that fish can understand in the event
    that the show will be serialized for fish.
    """
    def __init__(self, scene: "Scene", filter_id: str, filter_type: int, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, filter_type, pos)

    @abc.abstractmethod
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        """
        This method shall be consulted by the show file generator if it serializes the show in order to send it to fish.
        The purpose of this method is to translate the virtual filter output port to the filterid:portid string of the
        actually instantiated corresponding filter. It should return None, if and only if the provided input
        virtual_port_id does not exist with this filter type.

        :param virtual_port_id: The name of the port of this virtual filter that should be translated to the channel id
        of an instantiated filter.
        :returns: The resolved real filter and output port combination or None if the input was invalid.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def instantiate_filters(self, filter_list: list[Filter]):
        """
        This method will be called by the show file serializer when it serializes the show for fish. It places the real
        filters inside the provided filter_list argument.

        :param filter_list: The list to resolve the real filters into

        :note: Implementing classes do not need to resolve real port addresses from other filters themselves as this
        method will be called prior to resolving filter addresses. Instead, instantiated filters need to contain the
        configured channel mappings.
        """
        raise NotImplementedError()
