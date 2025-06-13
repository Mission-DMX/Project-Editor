# coding=utf-8
"""Provides data structures with accessors and modifiers for DMX"""
from logging import getLogger
from types import MappingProxyType
from typing import Callable

from PySide6 import QtCore, QtGui

import proto.FilterMode_pb2
from .broadcaster import Broadcaster
from .device import Device
from .macro import Macro
from .ofl.fixture import UsedFixture
from .scene import Scene
from .universe import Universe

logger = getLogger(__file__)


class BoardConfiguration:
    """Board configuration of a show file."""

    def __init__(self, show_name: str = "", default_active_scene: int = 0, notes: str = ""):
        self._show_name: str = show_name
        self._default_active_scene: int = default_active_scene
        self._notes: str = notes
        self._scenes: list[Scene] = []
        self._scenes_index: dict[int, int] = {}
        self._devices: list[Device] = []
        self._universes: dict[int, "Universe"] = {}
        self._ui_hints: dict[str, str] = {}
        self._macros: list[Macro] = []

        self._show_file_path: str = ""
        self._broadcaster: Broadcaster = Broadcaster()

        self._broadcaster.add_universe.connect(self._add_universe)
        self._broadcaster.add_fixture.connect(self._add_fixture)
        self._broadcaster.scene_created.connect(self._add_scene)
        self._broadcaster.clear_board_configuration.connect(self._clear)
        self._broadcaster.delete_scene.connect(self._delete_scene)
        self._broadcaster.delete_universe.connect(self._delete_universe)
        self._broadcaster.device_created.connect(self._add_device)
        self._broadcaster.delete_device.connect(self._delete_device)

        self._filter_update_msg_register: dict[tuple[int, str], list[Callable]] = {}
        self._broadcaster.update_filter_parameter.connect(self._distribute_filter_update_message)

    def _clear(self):
        """This method resets the show data prior to loading a new one."""
        for scene in self._scenes:
            self._broadcaster.delete_scene.emit(scene)
        for universe in self._universes:
            self._broadcaster.delete_universe.emit(universe)
        for device in self._devices:
            self._broadcaster.delete_device.emit(device)
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)
        self.scenes.clear()
        self._universes.clear()
        self._devices.clear()
        self._show_name = ""
        self._default_active_scene = 0
        self._notes = ""
        self._scenes_index = {}
        self._ui_hints = {}
        self._show_file_path = ""
        self._filter_update_msg_register.clear()
        self._macros.clear()

    def _add_scene(self, scene: Scene):
        """Adds a scene to the list of scenes.
        
        Args:
            scene: The scene to be added.
        """
        self._scenes.append(scene)
        self._scenes_index[scene.scene_id] = len(self._scenes) - 1

    def _delete_scene(self, scene: Scene):
        """Removes the passed scene from the list of scenes.
        
        Args:
            scene: The scene to be removed.
        """
        self._scenes.remove(scene)
        self._scenes_index.pop(scene.scene_id)

    def _add_universe(self, universe: Universe):
        """Creates and adds a universe from passed patching universe.
        Args:
            universe: The universe to add.
        """
        self._universes.update({universe.id: universe})

    def _add_fixture(self, used_fixture: UsedFixture):
        self._broadcaster.fixtures.append(used_fixture)

    def _delete_universe(self, universe: Universe):
        """Removes the passed universe from the list of universes.
        
        Args:
            universe: The universe to be removed.
        """
        try:
            del self._universes[universe.id]
        except ValueError:
            logger.error("Unable to remove universe %s", universe.name)

    def _add_device(self, device: Device):
        """Adds the device to the board configuration.
        
        Args:
            device: The device to be added.
        """
        self._devices.append(device)

    def _delete_device(self, device: Device):
        """Removes the passed device from the list of devices.
        
        Args:
            device: The device to be removed.
        """
        pass

    def universe(self, universe_id: int) -> Universe | None:
        """Tries to find a universe by id.

        Arg:
            universe_id: The id of the universe requested.

        Returns:
            The universe if found, else None.
        """
        return self._universes.get(universe_id, None)

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
    def universes(self) -> MappingProxyType[int, Universe]:
        """The universes of the show"""
        return MappingProxyType(self._universes)

    @property
    def ui_hints(self) -> dict[str, str]:
        """UI hints for the show"""
        return self._ui_hints

    @property
    def broadcaster(self) -> Broadcaster:
        """The broadcaster the board configuration uses"""
        return self._broadcaster

    @property
    def file_path(self) -> str:
        """ path to the showfile"""
        return self._show_file_path

    @file_path.setter
    def file_path(self, new_path: str):
        """Update the show file path.
        :param new_path: The location to save the show file to"""
        self._show_file_path = new_path
        self._broadcaster.show_file_path_changed.emit(new_path)

    def get_scene_by_id(self, scene_id: int) -> Scene | None:
        """Returns the scene by her id"""
        looked_up_position = self._scenes_index.get(scene_id)
        if looked_up_position is not None:
            if looked_up_position < len(self._scenes):
                return self._scenes[looked_up_position]
        for scene in self._scenes:
            if scene.scene_id == scene_id:
                return scene
        return None

    def _distribute_filter_update_message(self, param: proto.FilterMode_pb2.update_parameter):
        """Find listeners to incoming filter update message and distribute it to them."""
        candidate_list = self._filter_update_msg_register.get((param.scene_id, param.filter_id))
        if candidate_list is not None:
            for c in candidate_list:
                c(param)

    def register_filter_update_callback(self, target_scene: int, target_filter_id: str, c: Callable):
        """
        Register a new callback for filter update messages.

        If filter update messages are received, they need to be routed to their intended destination. This is done using
        this registration method. Suitable callables receive the update message as a parameter.
        :param target_scene: The scene the callback belongs to.
        :param target_filter_id: The filter id to listen on.
        :param c: The callable to register.
        """
        callable_list = self._filter_update_msg_register.get((target_scene, target_filter_id))
        if callable_list is None:
            callable_list = []
            self._filter_update_msg_register[(target_scene, target_filter_id)] = callable_list
        if c not in callable_list:
            callable_list.append(c)

    def remove_filter_update_callback(self, target_scene: int, target_filter_id: str, c: Callable):
        """
        Remove a previously registered callback.
        :param target_scene: The scene the callback belongs to.
        :param target_filter_id: The filter id which it is listening on.
        :param c: The callable to be removed.
        """
        callable_list = self._filter_update_msg_register.get((target_scene, target_filter_id))
        if callable_list is None:
            return
        if c in callable_list:
            callable_list.remove(c)

    def add_macro(self, m: Macro):
        """
        Add a new macro to the show file.

        This method must be called from a QObject as it triggers an event.

        :param m: The macro to add.
        """
        new_index = len(self._macros)
        self._macros.append(m)
        self._broadcaster.macro_added_to_show_file.emit(new_index)

    def get_macro(self, macro_id: int | str) -> Macro | None:
        """Get the macro specified by its index.
        :returns: The macro or None if none was found."""
        if isinstance(macro_id, int):
            if macro_id >= len(self._macros):
                return None
            return self._macros[macro_id]
        elif isinstance(macro_id, str):
            for m in self._macros:
                if m.name == macro_id:
                    return m
        return None

    @property
    def macros(self) -> list[Macro]:
        """Get a list of registered macros."""
        return self._macros.copy()

    def next_universe_id(self) -> int:
        """next empty universe id"""
        nex_id = len(self._universes)
        while self._universes.get(nex_id):
            nex_id += 1
        return nex_id
