# coding=utf-8
"""Filter module"""

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


class Filter:
    """Filter for show file"""

    def __init__(self, scene: "Scene", filter_id: str, filter_type: int, pos=None):
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
        """The unique id/name of the filter."""
        return self._filter_id

    @filter_id.setter
    def filter_id(self, id_):
        self._filter_id = id_
        # TODO notify parent scene filter index
        # TODO notify ui widgets in parent scene

    @property
    def filter_type(self) -> int:
        """The type of the filter"""
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

    def copy(self, new_scene: "Scene" = None, new_id: str = None) -> "Filter":
        f = Filter(new_scene if new_scene else self.scene, self._filter_id if not new_id else new_id, self._filter_type, self._pos)
        f._channel_links = self.channel_links.copy()
        f._initial_parameters = self._initial_parameters.copy()
        f._filter_configurations = self._filter_configurations.copy()
        f._in_data_types = self._in_data_types.copy()
        f._out_data_types = self._out_data_types.copy()
        f._gui_update_keys = self._gui_update_keys.copy()
        return f
