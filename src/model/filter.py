# coding=utf-8
"""Filter module"""
from typing import TYPE_CHECKING
from enum import IntFlag, auto

if TYPE_CHECKING:
    from . import Scene

class DataType(IntFlag):
    """Data types used by filter channels"""
    DT_8_BIT = auto()
    DT_16_BIT = auto()
    DT_DOUBLE = auto()
    DT_COLOR = auto()
    DT_BOOL = auto()


class Filter:
    """Filter for show file"""

    def __init__(self, scene: "Scene", filter_id: str, filter_type: int, pos: tuple[float, float] = (0.0, 0.0)):
        self._scene: "Scene" = scene
        self._filter_id = filter_id
        self._filter_type = int(filter_type)
        self._pos: tuple[float, float] = pos
        self._channel_links: dict[str, str] = {}
        self._initial_parameters: dict[str, str] = {}
        self._filter_configurations: dict[str, str] = {}

    @property
    def scene(self) -> "Scene":
        """The scene the filter belongs to"""
        return self._scene

    @property
    def filter_id(self) -> str:
        """The unique id/name of the filter."""
        return self._filter_id

    @property
    def filter_type(self) -> int:
        """The type of the filter"""
        return self._filter_type

    @property
    def pos(self) -> tuple[float, float]:
        """The postition of the filter node inside the ui"""
        return self._pos

    @pos.setter
    def pos(self, pos: tuple[float, float]):
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
