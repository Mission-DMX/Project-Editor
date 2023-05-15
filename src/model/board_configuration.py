# coding=utf-8
"""Provides data structures with accessors and modifiers for DMX"""
from dataclasses import dataclass, field

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


# @dataclass
class Filter:
    def __init__(self, id: str, type: int, pos: tuple[float, float] = (0.0, 0.0)) -> None:
        self.id = id
        self.type = type
        self.channel_links: dict[str, str] = {}
        self.initial_parameters: dict[str, str] = {}
        self.filter_configurations: dict[str, str] = {}
        self.pos: tuple[float, float] = pos


@dataclass
class Scene:
    id: int
    human_readable_name: str
    flowchart: Flowchart
    filters: list[Filter] = field(default_factory=list)


@dataclass
class BoardConfiguration:
    scenes: list[Scene] = field(default_factory=list)
    devices: list[str] = field(default_factory=list)
    universes: list[Universe] = field(default_factory=list)
    ui_hints: dict[str, str] = field(default_factory=dict)
    show_name: str = "Show"
    default_active_scene: int = 0
    notes: str = ""
