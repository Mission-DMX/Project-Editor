# coding=utf-8
"""Provides data structures with accessors and modifiers for DMX"""
from dataclasses import dataclass, field
from typing import Any
from enum import IntFlag, auto

from pyqtgraph.flowchart.Flowchart import Flowchart

from model.universe import Universe

class Device:
    """A DMX device"""

    def __init__(self, name: str):
        self._name: str = name

    @property
    def name(self) -> str:
        """ID of the dmx device"""
        return self._name


class DataType(IntFlag):
    """Data types used by filter channels"""
    DT_8_BIT = auto()
    DT_16_BIT = auto()
    DT_DOUBLE = auto()
    DT_COLOR = auto()
    DT_BOOL = auto()

# @dataclass
class Filter:
    """Filter for show file
    
    Attributes:
        id: Unique id of the filter, used as its name
        type: Specifies filter
        pos: Tuple of its position inside the editor of format (x, y)
        channel_links: Dict containing entries of format (local_input, remote_name:remote_output)
        initial_parameters: Dict containing entries of format (parameter_name, parameter_value)
        filter_configuration: Dict containing entries of format (config_name, config_value)
    """
    def __init__(self, filter_id: str, filter_type: int, pos: tuple[float, float] = (0.0, 0.0)) -> None:
        self.filter_id = filter_id
        self.filter_type = int(filter_type)
        self.pos: tuple[float, float] = pos
        self.channel_links: dict[str, str] = {}
        self.initial_parameters: dict[str, str] = {}
        self.filter_configurations: dict[str, str] = {}


class UniverseFilter(Filter):
    """Special class for universe filters.
    
    Attributes:
        id: Unique id of the filter, used as its name
        board_configuration: Instance of the currently loaded board configuratuon.
        pos: Tuple of its position inside the editor of format (x, y)
    """
    def __init__(self, filter_id: str, board_configuration: Any = None, pos: tuple[float, float] = (0, 0)) -> None:
        super().__init__(filter_id, 11, pos)

        # Needed to show and configure universe properties
        self._board_configuration: BoardConfiguration = board_configuration

    @property
    def board_configuration(self):
        """
        Returns:
            The current board configuration this filter is part of
        """
        if self._board_configuration is None:
            raise AttributeError("You must add the board_configuration to a universe filter.")
        return self._board_configuration

    @board_configuration.setter
    def board_configuration(self, board_configuration):
        """Sets the current board configuration this filter is part of"""
        self._board_configuration = board_configuration


@dataclass
class Scene:
    """Scene for show file.
    
    Attributes:
        id: Unique id of the scene
        human_readable_name: The name that is displayed inside a ui
        flowchart: The flowchart that represents the scenes filters
        board_configuration: The board configuration the scene is part of
        filters: List of all the filters that are part of the scene
    """
    id: int
    human_readable_name: str

    # Needed to add nodes when loading show files
    flowchart: Flowchart
    board_configuration: Any
    filters: list[Filter] = field(default_factory=list)


@dataclass
class BoardConfiguration:
    """Board configuration of a show file.
    
    Attributes:
        show_name: The human readabel name of the show
        default_active_scene: ID of the scene to be loaded in the beginning
        notes: Optional notes
        scenes: List of all the scenes that are part of the board configuration
        devices: List of all the devices that are part of the board configuration
        universes: List of all the universes that are part of the board configuration
        ui_hints: List of all the ui hints for the board configuration
    """
    show_name: str = "Show"
    default_active_scene: int = 0
    notes: str = ""
    scenes: list[Scene] = field(default_factory=list)
    devices: list[str] = field(default_factory=list)
    universes: list[Universe] = field(default_factory=list)
    ui_hints: dict[str, str] = field(default_factory=dict)
