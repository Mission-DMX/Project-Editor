"""Provides data structures with accessors and modifiers for DMX."""

from collections.abc import Callable, Sequence
from logging import getLogger

import numpy as np
from PySide6 import QtCore, QtGui

import proto.FilterMode_pb2

from .broadcaster import Broadcaster
from .device import Device
from .macro import Macro
from .ofl.fixture import UsedFixture
from .scene import Scene
from .universe import Universe

logger = getLogger(__name__)


class BoardConfiguration:
    """Board configuration of a show file."""

    def __init__(self, show_name: str = "", default_active_scene: int = 0, notes: str = "") -> None:
        """Initialize broadcaster singleton."""
        self._show_name: str = show_name
        self._default_active_scene: int = default_active_scene
        self._notes: str = notes
        self._scenes: list[Scene] = []
        self._scenes_index: dict[int, int] = {}
        self._devices: list[Device] = []
        self._universes: dict[int, Universe] = {}
        self._fixtures: list[UsedFixture] = []
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

        self._filter_update_msg_register: dict[tuple[int, str], set[Callable]] = {}
        self._broadcaster.update_filter_parameter.connect(self._distribute_filter_update_message)

    def _clear(self) -> None:
        """Reset the show data before loading a new one."""
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

    def _add_scene(self, scene: Scene) -> None:
        """Add a scene to the list of scenes.

        Args:
            scene: The scene to be added.

        """
        self._scenes.append(scene)
        self._scenes_index[scene.scene_id] = len(self._scenes) - 1

    def _delete_scene(self, scene: Scene) -> None:
        """Remove the passed scene from the list of scenes.

        Args:
            scene: The scene to be removed.

        """
        self._scenes.remove(scene)
        self._scenes_index.pop(scene.scene_id)

    def _add_universe(self, universe: Universe) -> None:
        """Create and add a universe.

        Args:
            universe: The universe to add.

        """
        self._universes.update({universe.id: universe})

    def _add_fixture(self, used_fixture: UsedFixture) -> None:
        self._fixtures.append(used_fixture)

    def _delete_universe(self, universe: Universe) -> None:
        """Remove the passed universe from the list of universes.

        Args:
            universe: The universe to be removed.

        """
        try:
            del self._universes[universe.id]
        except ValueError:
            logger.exception("Unable to remove universe %s", universe.name)

    def _add_device(self, device: Device) -> None:
        """Add a device to the board configuration.

        Args:
            device: The device to be added.

        """
        self._devices.append(device)

    def _delete_device(self, device: Device) -> None:
        """Remove the passed device from the list of devices.

        Args:
            device: The device to be removed.

        """

    def universe(self, universe_id: int) -> Universe | None:
        """Try to find a universe by id.

        Args:
            universe_id: The id of the universe requested.

        Returns:
            The universe if found, else None.

        """
        return self._universes.get(universe_id, None)

    @property
    def fixtures(self) -> Sequence[UsedFixture]:
        """Fixtures associated with this Show."""
        return self._fixtures

    @property
    def show_name(self) -> str:
        """The name of the show."""
        return self._show_name

    @show_name.setter
    def show_name(self, show_name: str) -> None:
        self._show_name = show_name

    @property
    def default_active_scene(self) -> int:
        """Scene to be activated by fish on loadup."""
        return self._default_active_scene

    @default_active_scene.setter
    def default_active_scene(self, default_active_scene: int) -> None:
        self._default_active_scene = default_active_scene

    @property
    def notes(self) -> str:
        """Notes for the show."""
        return self._notes

    @notes.setter
    def notes(self, notes: str) -> None:
        self._notes = notes

    @property
    def scenes(self) -> list[Scene]:
        """The scenes of the show."""
        return self._scenes

    @property
    def devices(self) -> list[Device]:
        """The devices of the show."""
        return self._devices

    @property
    def universes(self) -> list[Universe]:
        """The universes of the show."""
        return list(self._universes.values())

    @property
    def ui_hints(self) -> dict[str, str]:
        """UI hints for the show."""
        return self._ui_hints

    @property
    def broadcaster(self) -> Broadcaster:
        """The broadcaster the board configuration uses."""
        return self._broadcaster

    @property
    def file_path(self) -> str:
        """Path to the showfile."""
        return self._show_file_path

    @file_path.setter
    def file_path(self, new_path: str) -> None:
        self._show_file_path = new_path
        self._broadcaster.show_file_path_changed.emit(new_path)

    def get_scene_by_id(self, scene_id: int) -> Scene | None:
        """Get a scene by her id."""
        looked_up_position = self._scenes_index.get(scene_id)
        if looked_up_position is not None and looked_up_position < len(self._scenes):
            return self._scenes[looked_up_position]
        for scene in self._scenes:
            if scene.scene_id == scene_id:
                return scene
        return None

    def _distribute_filter_update_message(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Find listeners to incoming filter update message and distribute it to them."""
        candidate_list = self._filter_update_msg_register.get((param.scene_id, param.filter_id))
        if candidate_list is not None:
            for c in candidate_list:
                c(param)

    def register_filter_update_callback(self, target_scene: int, target_filter_id: str, c: Callable) -> None:
        """Register a new callback for filter update messages.

        If filter update messages are received, they need to be routed to their intended destination. This is done using
        this registration method. Suitable callables receive the update message as a parameter.

        Args:
            target_scene: The scene the callback belongs to.
            target_filter_id: The filter id to listen on.
            c: The callable to register.

        """
        callable_list = self._filter_update_msg_register.get((target_scene, target_filter_id))
        if callable_list is None:
            callable_list = set()
            self._filter_update_msg_register[(target_scene, target_filter_id)] = callable_list
        if c not in callable_list:
            callable_list.add(c)

    def remove_filter_update_callback(self, target_scene: int, target_filter_id: str, c: Callable) -> None:
        """Remove a previously registered callback.

        Args:
            target_scene: The scene the callback belongs to.
            target_filter_id: The filter id which it is listening on.
            c: The callable to be removed.

        """
        callable_list = self._filter_update_msg_register.get((target_scene, target_filter_id))
        if callable_list is None:
            return
        if c in callable_list:
            callable_list.remove(c)

    def add_macro(self, macro: Macro) -> None:
        """Add a new macro to the show file.

        This method must be called from a QObject as it triggers an event.

        Args:
            macro: The macro to add.

        """
        new_index = len(self._macros)
        self._macros.append(macro)
        self._broadcaster.macro_added_to_show_file.emit(new_index)

    def get_macro(self, macro_id: int | str) -> Macro | None:
        """Macro specified by its index.

        Returns:
            The macro or None if no macro was found.

        """
        if isinstance(macro_id, int):
            if macro_id >= len(self._macros):
                return None
            return self._macros[macro_id]
        if isinstance(macro_id, str):
            for m in self._macros:
                if m.name == macro_id:
                    return m
        return None

    @property
    def macros(self) -> list[Macro]:
        """Get a list of registered macros."""
        return self._macros.copy()

    def next_universe_id(self) -> int:
        """Next empty universe id."""
        nex_id = len(self._universes)
        while self._universes.get(nex_id):
            nex_id += 1
        return nex_id

    def get_occupied_channels(self, universe_id: int) -> np.typing.NDArray[int]:
        """List of all channels that are occupied by a scene."""
        ranges = [
            np.arange(fixture.start_index, fixture.start_index + fixture.channel_length)
            for fixture in self.fixtures
            if fixture.universe_id == universe_id
        ]

        return np.concatenate(ranges) if ranges else np.array([], dtype=int)
