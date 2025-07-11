from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog, QWidget

    from controller.network import NetworkManager
    from model import Broadcaster, Filter
    from model.scene import Scene

_network_manager_instance: NetworkManager = None


def setup_network_manager(nm: NetworkManager, b: Broadcaster) -> None:
    global _network_manager_instance
    _network_manager_instance = nm
    b.request_main_brightness_fader_update.connect(nm.set_main_brightness_fader_position)


class UIWidget(ABC):
    """This class represents a link between an interactable widget on a page and the corresponding filter."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """ Set up the basic components of a widget.

        Arguments:
            fid -- The id of the corresponding filter.
        """
        self._position: tuple[int, int] = (0, 0)
        self._size: tuple[int, int] = (0, 0)
        self._associated_filters: dict[str, str] = {}
        if isinstance(configuration, dict):
            self._configuration: dict[str, str] = configuration.copy()
        else:
            self._configuration = {}
        self._parent = parent_page

    @abstractmethod
    def generate_update_content(self) -> list[tuple[str, str]]:
        """This method needs to be implemented in order to compute the update content.

        Returns:
            A list of key-value-tuples where each tuple defines a parameter of the filter to be updated.
        """
        raise NotImplementedError

    @abstractmethod
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """This method needs to yield a QWidget that can be placed on the player page.

        Returns:
            A fully set up QWidget instance
        """
        raise NotImplementedError

    @abstractmethod
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """This method needs to return a QWidget that can be used to configure the UI widget within
        the UI editor.

        Returns:
            A fully set up QWidget instance
        """
        raise NotImplementedError

    def set_filter(self, f: Filter, i: int) -> None:
        if not f:
            return
        self.associated_filters[str(i)] = f.filter_id

    @property
    def filter_ids(self) -> list[str]:
        """Get the id of the linked filter"""
        linked_filters: list[str | None] = [None] * len(self._associated_filters)

        for i, k, v in enumerate(self._associated_filters.items()):
            try:
                ik = int(k)
            except ValueError:
                ik = i
            if linked_filters[ik] is not None:
                linked_filters[ik] = v
            else:
                for j in range(len(linked_filters)):
                    if linked_filters[j] is None:
                        linked_filters[j] = v
                        break

        while None in linked_filters:
            linked_filters.remove(None)
        return linked_filters

    @property
    def associated_filters(self) -> dict[str, str]:
        return self._associated_filters

    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """This method will be called by the parent scene in the event of the renaming of a filter. It may be overridden
        in order to implement special behaviour"""
        for slot in self._associated_filters:
            if self._associated_filters[slot] == old_id:
                self._associated_filters[slot] = new_id

    @property
    def parent(self) -> UIPage:
        """Get the parent page of this widget"""
        return self._parent

    @property
    def position(self) -> tuple[int, int]:
        """Get the position of the widget on the UI page"""
        return self._position

    @position.setter
    def position(self, new_position: tuple[int, int]) -> None:
        """Update the position of the widget on the UI page"""
        self._position = new_position
        self.parent.display_update_required = True

    @property
    def size(self) -> tuple[int, int]:
        """Get the size of the widget in the UI page"""
        return self._size

    @size.setter
    def size(self, new_size: tuple[int, int]) -> None:
        """Update the size of the widget"""
        self._size = new_size
        self.parent.display_update_required = True

    @property
    def configuration(self) -> dict[str, str]:
        return self._configuration

    def copy_base(self, w: UIWidget) -> UIWidget:
        w._position = self._position
        w._size = self._size
        w._filter_id = self._filter_id
        w._configuration = self._configuration.copy()
        return w

    @abstractmethod
    def copy(self, new_parent: UIPage) -> UIWidget:
        """This method needs to perform a deep copy of the object, excluding generatable state, such as the widgets"""
        raise NotImplementedError

    @abstractmethod
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        """This method shall return a widget that will be placed within the configuration dialog"""
        # TODO warum nutzt nur eine der implementierenden klassen überhaupt das parent objekt?
        raise NotImplementedError

    def get_variante(self) -> str:
        """This method needs to be overridden if there are multiple fitting widgets for a filter
        type in order for the show file saving (and loading) to choose the correct one."""
        return ""

    def push_update(self) -> None:
        """Use this method to trigger a filter update process"""
        for entry in self.generate_update_content():
            k = entry[0]
            v = entry[1]
            if ":" in k:
                split_key = k.split(":")
                target_fid = split_key[0]
                k = split_key[1]
            else:
                target_fid = self.filter_ids[0]
            _network_manager_instance.send_gui_update_to_fish(self.parent.scene.scene_id, target_fid, k, v)


class UIPage:
    """This class represents a page containing widgets that can be used to control the show."""

    def __init__(self, parent: Scene) -> None:
        """Construct a UI Page

        Arguments:
            sid -- The id of the scene where the corresponding filter is located.
        """
        self._widgets: list[UIWidget] = []
        self._parent_scene: Scene = parent
        self._title: str = ""
        self._player: str | None = None
        self.display_update_required = False

    @property
    def scene(self) -> Scene:
        """Get the scene this page is bound to"""
        return self._parent_scene

    @property
    def page_active_on_player(self) -> bool:
        """Returns true if this page is currently displayed on any player"""
        return self._player is not None

    def activate_on_player(self, player: str) -> None:
        """Set the player this page is displayed on"""
        self._player = player
        # TODO push page to player

    @property
    def widgets(self) -> list[UIWidget]:
        """Returns a copy of the internal widget list"""
        return list(self._widgets)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, new_title: str) -> None:
        self._title = new_title

    def copy(self, new_parent: Scene) -> UIPage:
        new_page = UIPage(new_parent)
        new_page._player = self._player
        new_page._title = self._title
        for w in self._widgets:
            new_page._widgets.append(w.copy(new_page))
        return new_page

    def append_widget(self, widget: UIWidget) -> None:
        self._widgets.append(widget)

    def push_update(self) -> None:
        """This method indicates that updates to the running filters should be sent."""

    def remove_widget(self, widget: UIWidget) -> None:
        self._widgets.remove(widget)


class ShowUI:
    """This class contains all pages of the show

    The _page_storage variable contains the pages per scene.
    """
    _fish_connector: NetworkManager = None

    def __init__(self) -> None:
        """This constructor initializes the show UI.

        At any given time there may only be one instance of this class running in the player but one might construct
        arbitrary amounts for editing purposes.
        """
        # List of scene tuples. A scene tuple consists out of the scene name and a list of associated UI pages.
        self._page_storage: list[tuple[str, list[UIPage]]] = []
        self._active_scene: int = 0

    @property
    def active_scene(self) -> int:
        """Get the index of the current active scene"""
        return self._active_scene

    @active_scene.setter
    def active_scene(self, scene: int) -> None:
        """Set the current active scene.

        Warning: setting this property will actually update the current active scene, if this UI is the active one.
        """
        if scene < 0 or scene >= len(self._page_storage):
            raise ValueError("Scene index out of range")
        self._active_scene = scene
        # TODO change scene if active show running
        # TODO notify player about UI update, distribute pages to available players.

    @property
    def scenes(self) -> list[str]:
        scene_name_list = []
        for scene_name, _ in self._page_storage:
            scene_name_list.append(scene_name)
        return scene_name_list

    @property
    def pages(self) -> list[UIPage]:
        """This method enumerates all pages.

        Returns:
            The complete list of pages.
        """
        return [p for _, pl in self._page_storage for p in pl]

    # @staticmethod
    # @property
    # def network_connection() -> NetworkManager:
    #    """Get the linked network manager"""
    #    return ShowUI._fish_connector

    # @staticmethod
    # @network_connection.setter
    # def network_connection(self, fish_connector: NetworkManager):
    #    """Set the linked network manager"""
    #    ShowUI._fish_connector = fish_connector
