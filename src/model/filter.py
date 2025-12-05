# pylint: disable=implicit-flag-alias
"""Filter model.

Contains: DataType, FilterTypeEnumeration, Filter and VirtualFilter
"""

from __future__ import annotations

import abc
from enum import IntFlag, auto
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from . import Scene


class DataType(IntFlag):
    """Data types used by filter channels."""

    DT_8_BIT = auto()
    DT_16_BIT = auto()
    DT_DOUBLE = auto()
    DT_COLOR = auto()
    DT_BOOL = auto()

    def format_for_filters(self) -> str:
        """Datatype representation commonly used by the fish filters for configuration."""
        if self.value == DataType.DT_8_BIT.value:
            return "8bit"

        if self.value == DataType.DT_16_BIT.value:
            return "16bit"

        if self.value == DataType.DT_DOUBLE.value:
            return "float"

        if self.value == DataType.DT_COLOR.value:
            return "color"

        return "8bit"  # bools are 8 bit

    @staticmethod
    def names() -> list[str]:
        """List of all available data type names."""
        return [
            f.format_for_filters()
            for f in [DataType.DT_8_BIT, DataType.DT_16_BIT, DataType.DT_DOUBLE, DataType.DT_COLOR]
        ]

    @staticmethod
    def from_filter_str(type_definition_string: str) -> DataType:
        """Deserialize from filter string.

        Throws:
            ValueError if the type definition string is invalid.

        """
        if isinstance(type_definition_string, DataType):
            return type_definition_string
        match type_definition_string.lower():
            case "8bit":
                return DataType.DT_8_BIT
            case "16bit":
                return DataType.DT_16_BIT
            case "float":
                return DataType.DT_DOUBLE
            case "color":
                return DataType.DT_COLOR
            case _:
                raise ValueError(f"Unknown filter type: {type_definition_string}")

    def __str__(self) -> str:
        """Get a human-readable representation of the data type."""
        if self.value == DataType.DT_BOOL.value:
            return "bool (8bit)"
        return self.format_for_filters()


class FilterTypeEnumeration(IntFlag):
    """Filter type enumeration.

    Negative values indicate virtual filters.
    """

    VFILTER_FADER_RAW = -39
    VFILTER_FADER_HSI = -40
    VFILTER_FADER_HSIA = -41
    VFILTER_FADER_HSIU = -42
    VFILTER_FADER_HSIAU = -43

    VFILTER_SEQUENCER = -12
    VFILTER_COLOR_MIXER = -11
    VFILTER_IMPORT = -10
    VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN = -9
    VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE = -8
    VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE = -7
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
    FILTER_TRIGONOMETRICS_SIN = 19
    FILTER_TRIGONOMETRICS_COSIN = 20
    FILTER_TRIGONOMETRICS_TANGENT = 21
    FILTER_TRIGONOMETRICS_ARCSIN = 22
    FILTER_TRIGONOMETRICS_ARCCOSIN = 23
    FILTER_TRIGONOMETRICS_ARCTANGENT = 24
    FILTER_WAVES_SQUARE = 25
    FILTER_WAVES_TRIANGLE = 26
    FILTER_WAVES_SAWTOOTH = 27
    FILTER_ARITHMETICS_LOGARITHM = 28
    FILTER_ARITHMETICS_EXPONENTIAL = 29
    FILTER_ARITHMETICS_MINIMUM = 30
    FILTER_ARITHMETICS_MAXIMUM = 31
    FILTER_TYPE_TIME_INPUT = 32
    FILTER_TIME_SWITCH_ON_DELAY_8BIT = 33
    FILTER_TIME_SWITCH_ON_DELAY_16BIT = 34
    FILTER_TIME_SWITCH_ON_DELAY_FLOAT = 35
    FILTER_TIME_SWITCH_OFF_DELAY_8BIT = 36
    FILTER_TIME_SWITCH_OFF_DELAY_16BIT = 37
    FILTER_TIME_SWITCH_OFF_DELAY_FLOAT = 38
    FILTER_FADER_RAW = 39
    FILTER_FADER_HSI = 40
    FILTER_FADER_HSIA = 41
    FILTER_FADER_HSIU = 42
    FILTER_FADER_HSIAU = 43
    FILTER_TYPE_CUES = 44
    FILTER_EFFECT_SHIFT_8BIT = 45
    FILTER_EFFECT_SHIFT_16BIT = 46
    FILTER_EFFECT_SHIFT_FLOAT = 47
    FILTER_EFFECT_SHIFT_COLOR = 48
    FILTER_TYPE_MAIN_BRIGHTNESS = 49
    FILTER_SCRIPTING_LUA = 50
    FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT = 51
    FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT = 52
    FILTER_ADAPTER_COLOR_TO_FLOAT = 53
    FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE = 54
    FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE = 55
    FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE = 56
    FILTER_ADAPTER_DUAL_BYTE_TO_16BIT = 57
    FILTER_ADAPTER_8BIT_TO_16BIT = 58
    FILTER_COLOR_MIXER_HSV = 59
    FILTER_COLOR_MIXER_ADDITIVE_RGB = 60
    FILTER_COLOR_MIXER_NORMATVE_RGB = 61
    FILTER_SUM_8BIT = 62
    FILTER_SUM_16BIT = 63
    FILTER_SUM_FLOAT = 64
    FILTER_REMOTE_DEBUG_8BIT = 65
    FILTER_REMOTE_DEBUG_16BIT = 66
    FILTER_REMOTE_DEBUG_FLOAT = 67
    FILTER_REMOTE_DEBUG_PIXEL = 68
    FILTER_SEQUENCER = 69
    FILTER_EVENT_COUNTER = 70


class Filter:
    """Filter for a show file."""

    def __init__(
        self,
        scene: Scene,
        filter_id: str,
        filter_type: int,
        pos: tuple[int, int] | tuple[float, float] | None = None,
        filter_configurations: dict[str, str] | None = None,
        initial_parameters: dict[str, str] | None = None,
    ) -> None:
        """Filter for a show file.

        Args:
        scene: The parent scene of the filter.
        filter_id: The ID of the filter.
        filter_type: The type of the filter.
        pos: The position of the filter in the node editor.
        filter_configurations: The configuration of the filter.
        initial_parameters: The initial parameters of the filter.

        """
        # TODO id why as string
        if pos is None:
            pos = [0.0, 0.0]

        self._scene: Scene = scene
        self._filter_id = filter_id
        self._filter_type: int = int(filter_type)
        self._pos: tuple[float, float] | None = pos
        self._channel_links: dict[str, str] = {}
        self._initial_parameters: dict[str, str] = initial_parameters or {}
        self._filter_configurations: dict[str, str] = filter_configurations or {}
        self._gui_update_keys: dict[str, Union[DataType, list[str]]] = {}
        self._in_data_types: dict[str, DataType] = {}
        self._default_values: dict[str, str] = {}
        self._out_data_types: dict[str, DataType] = {}
        self._configuration_supported: bool = True

    @property
    def scene(self) -> Scene:
        """The scene the filter belongs to."""
        return self._scene

    @property
    def configuration_supported(self) -> bool:
        """Returns true if the filter supports user configuration."""
        return self._configuration_supported

    @property
    def filter_id(self) -> str:
        """The unique id/name of the filter. This is not to be confused with the filter type."""
        return self._filter_id

    @filter_id.setter
    def filter_id(self, id_: str) -> None:
        old_id: str = self._filter_id
        self._filter_id = id_
        if self.scene:
            self.scene.notify_about_filter_rename_action(self, old_id)

    @property
    def filter_type(self) -> int:
        """The type of the filter.

        This might be a positive number for a filter that fish understands or a negative
        one in case of a virtual filter that the GUI needs to resolve first.
        """
        return self._filter_type

    @filter_type.setter
    def filter_type(self, type_: int) -> None:
        self._filter_type = type_

    @property
    def pos(self) -> tuple[float, float] | None:
        """The position of the filter node inside the ui."""
        return self._pos

    @pos.setter
    def pos(self, pos: tuple[float, float] | None) -> None:
        self._pos = pos

    @property
    def channel_links(self) -> dict[str, str]:
        """Dict mapping the filter inputs to the connected outputs."""
        return self._channel_links

    @property
    def initial_parameters(self) -> dict[str, str]:
        """The initial parameters."""
        return self._initial_parameters

    @property
    def filter_configurations(self) -> dict[str, str]:
        """The filter configurations."""
        return self._filter_configurations

    @property
    def in_data_types(self) -> dict[str, DataType]:
        """Dict mapping input channel names to their data types."""
        return self._in_data_types

    @property
    def default_values(self) -> dict[str, str]:
        """Dict mapping input channel names to their data types."""
        return self._default_values

    @property
    def out_data_types(self) -> dict[str, DataType]:
        """Dict mapping output channel names to their data types."""
        return self._out_data_types

    @property
    def gui_update_keys(self) -> dict[str, DataType | str]:
        """Get updates that should be transmitted to the filter currently running on fish."""
        return self._gui_update_keys

    @property
    def is_virtual_filter(self) -> bool:
        """Returns true if the filter has an ID from the virtual range."""
        return self.filter_type < 0

    def copy(self, new_scene: Scene = None, new_id: str | None = None) -> Filter:
        """Copy the filter.

        Args:
            new_scene: Parent scene of the new filter object.
            new_id: New id of the new filter object.

        """
        from .virtual_filters.vfilter_factory import construct_virtual_filter_instance

        if self.is_virtual_filter:
            f = construct_virtual_filter_instance(
                new_scene if new_scene else self.scene,
                self._filter_type,
                new_id if new_id else self._filter_id,
                pos=self._pos,
            )
            f.filter_configurations.update(self.filter_configurations.copy())
        else:
            f = Filter(
                new_scene if new_scene else self.scene,
                new_id if new_id else self._filter_id,
                self._filter_type,
                self._pos,
                self.filter_configurations.copy(),
            )
        f._channel_links = self.channel_links.copy()
        f._initial_parameters = self.initial_parameters.copy()
        f._in_data_types = self._in_data_types.copy()
        f._out_data_types = self._out_data_types.copy()
        f._gui_update_keys = self._gui_update_keys.copy()
        f._default_values = self._default_values.copy()
        if isinstance(f, VirtualFilter):
            f.deserialize()
        return f

    def __str__(self) -> str:
        """Get a human-readable representation of this filter."""
        return f"Filter '{self._filter_id}' from scene '{self.scene}'"


class VirtualFilter(Filter, abc.ABC):
    """Abstract class can be used to implement virtual filters.

    The configuration of these filters is still
    stored within the filter configuration; however, these filters will not be sent to fish. Instead, their
    instantiate_filters method will be called to provide a representation that fish can understand in the event
    that the show will be serialized for fish.
    """

    def __init__(self, scene: Scene, filter_id: str, filter_type: int, pos: tuple[int] | None = None) -> None:
        """Initialize a virtual filter.

        Args:
            scene: The scene this filter belongs to.
            filter_id: The unique ID of the filter.
            filter_type: The type of the filter.
            pos: The position of the filter node inside the UI.

        """
        super().__init__(scene, filter_id, filter_type, pos)

    @abc.abstractmethod
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        """Shall be consulted by the show file generator if it serializes the show to send it to fish.

        The purpose of this method is to translate the virtual filter output port to the filterid:portid string of the
        actually instantiated corresponding filter. It should return None if and only if the provided input
        virtual_port_id does not exist with this filter type.

        Args:
            virtual_port_id: The name of the port of this virtual filter that should be translated to the channel id
                                of an instantiated filter.

        Returns: The resolved real filter and output port combination or None if the input was invalid.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        """Will be called by the show file serializer when it serializes the show for fish.

        It places the real filters inside the provided filter_list argument.

        Notes:
            Implementing classes do not need to resolve real port addresses from other filters themselves as this
            method will be called prior to resolving filter addresses. Instead, instantiated filters need to contain the
            configured channel mappings.

        Args:
            filter_list: The list to resolve the real filters into

        """
        raise NotImplementedError

    def deserialize(self) -> None:
        """Perform post-processing after the filter configuration has been loaded.

        Use this method to implement the loading of the filter model.
        """

    def serialize(self) -> None:
        """Virtual filter might need to prepare themselves prior to being saved to a show file.

        For example, they might need to compile some information. This method will be called just prior to generating
        the filter element within the show file. Afterward the current state of the v-filter needs to be accessible
        purely by querying the configuration and parameters variables.
        """
