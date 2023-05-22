# coding=utf-8
"""Provides data structures with accessors and modifiers for DMX"""
from .universe import Universe
from .scene import Scene
from .broadcaster import Broadcaster
from .patching_universe import PatchingUniverse
from .device import Device


class BoardConfiguration:
    """Board configuration of a show file."""
    def __init__(self, broadcaster: Broadcaster, show_name: str = "", default_active_scene: int = 0, notes: str = ""):
        self._show_name: str = show_name
        self._default_active_scene: int = default_active_scene
        self._notes: str = notes
        self._scenes: list[Scene] = []
        self._devices: list[str] = []
        self._universes: list[Universe] = []
        self._ui_hints: dict[str, str] = {}

        self._broadcaster:  Broadcaster = broadcaster

        self._broadcaster.add_universe.connect(self._add_universe)
        self._broadcaster.scene_created.connect(self._add_scene)
        self._broadcaster.clear_board_configuration.connect(self._clear)
        self._broadcaster.delete_scene.connect(self._delete_scene)
        self._broadcaster.delete_universe.connect(self._delete_universe)

    def _add_universe(self, patching_universe: PatchingUniverse):
        """Creates and adds a universe from passed patching universe"""
        universe = Universe(patching_universe)
        self._universes.append(universe)

    def _add_scene(self, scene: Scene):
        """Adds a scene to the list of scenes"""
        self._scenes.append(scene)

    def _clear(self):
        """Clears all properties/sets them to default values"""
        self._show_name = ""
        self._default_active_scene = 0
        self._notes = ""
        self._scenes = []
        self._devices = []
        self._universes = []
        self._ui_hints = {}

    def _delete_scene(self, scene: Scene):
        """Removes the passed scene from the list of scenes"""
        self._scenes.remove(scene)

    def _delete_universe(self, universe: Universe):
        """Removes the passed universe from the list of universes"""
        self._universes.remove(universe)

    @property
    def show_name(self) -> str:
        """The name of the show"""
        return self._show_name

    @show_name.setter
    def show_name(self, show_name: str):
        """Sets the show name"""
        self._show_name = show_name

    @property
    def default_active_scene(self) -> int:
        """Scene to be activated by fish on loadup"""
        return self._default_active_scene

    @default_active_scene.setter
    def default_active_scene(self, default_active_scene: int):
        """Setss the scene to be activated by fish on loadup"""
        self._default_active_scene = default_active_scene

    @property
    def notes(self) -> str:
        """Notes for the show"""
        return self._notes

    @notes.setter
    def notes(self, notes: str):
        """Sets the notes for the show"""
        self._notes = notes

    @property
    def scenes(self) -> list[Scene]:
        """The scenes of the show"""
        return self._scenes

    @property
    def devices(self) -> list[Device]:
        """The devices of the show"""
        return self._devices

    @property
    def universes(self) -> list[Universe]:
        """The universes of the show"""
        return self._universes

    @property
    def ui_hints(self) -> dict[str, str]:
        """UI hints for the show"""
        return  self._ui_hints

    @property
    def broadcaster(self) -> Broadcaster:
        """The broadcaster the board configuration uses"""
        return self._broadcaster
