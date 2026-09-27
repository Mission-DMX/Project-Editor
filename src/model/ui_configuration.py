"""Contains the show UI model.

Classes:
    UIWidget -- An ABC for a show UI widget.
    UIPage -- A page containing widgets.
    ShowUI -- Container class for all pages in the scene.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING

from controller.network import NetworkManager

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog, QWidget

    import proto.FilterMode_pb2
    from model import Filter
    from model.scene import Scene

logger = getLogger(__name__)

class UIWidget(ABC):
    """Show UI widget.

    This class represents a link between an interactable widget on a page and the corresponding filter.
    """

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Set up the basic components of a widget.

        Arguments:
            parent_page: The parent page of the widget.
            configuration: The configuration of the widget.

        """
        self._position: tuple[int, int] = (0, 0)
        self._size: tuple[int, int] = (0, 0)
        self._associated_filters: dict[str, str] = {}
        if isinstance(configuration, dict):
            self._configuration: dict[str, str] = configuration.copy()
        else:
            self._configuration = {}
        self._parent = parent_page
        self._network_manager = NetworkManager()

    @abstractmethod
    def generate_update_content(self) -> list[tuple[str, str]]:
        """Get the updates to be sent to fish.

        This method needs to be implemented in order to compute the update content.

        Returns:
            A list of key-value-tuples where each tuple defines a parameter of the filter to be updated.

        """
        raise NotImplementedError

    @abstractmethod
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Get the show UI widget.

        This method needs to yield a QWidget that can be placed on the player page.

        Returns:
            A fully set up QWidget instance

        """
        raise NotImplementedError

    @abstractmethod
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Get the configuration widget.

        This method needs to return a QWidget that can be used to configure the UI widget within
        the UI editor.

        Returns:
            A fully set up QWidget instance

        """
        raise NotImplementedError

    def set_filter(self, f: Filter, i: int) -> None:
        """Set an associated filter.

        Args:
            i: The filter index to update.
            f: The new filter to use.

        """
        if not f:
            return
        self.associated_filters[str(i)] = f.filter_id

    @property
    def filter_ids(self) -> list[str]:
        """Get the id of the linked filter."""
        linked_filters: list[str | None] = [None] * len(self._associated_filters)

        for i, (k, v) in enumerate(self._associated_filters.items()):
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
        return [linked_filter for linked_filter in linked_filters if linked_filter is not None]

    @property
    def associated_filters(self) -> dict[str, str]:
        """Get the filters associated with this show UI widget."""
        return self._associated_filters

    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """Notify widget of renamed filter ids.

        This method will be called by the parent scene in the event of the renaming of a filter. It may be overridden
        in order to implement special behaviour
        """
        for slot in self._associated_filters:
            if self._associated_filters[slot] == old_id:
                self._associated_filters[slot] = new_id

    @property
    def parent(self) -> UIPage:
        """Get the parent page of this widget."""
        return self._parent

    @property
    def position(self) -> tuple[int, int]:
        """Get the position of the widget on the UI page."""
        return self._position

    @position.setter
    def position(self, new_position: tuple[int, int]) -> None:
        """Update the position of the widget on the UI page."""
        self._position = new_position
        self.parent.display_update_required = True

    @property
    def size(self) -> tuple[int, int]:
        """Get the size of the widget in the UI page."""
        return self._size

    @size.setter
    def size(self, new_size: tuple[int, int]) -> None:
        """Update the size of the widget."""
        self._size = new_size
        self.parent.display_update_required = True

    @property
    def configuration(self) -> dict[str, str]:
        """Get the configuration of the widget."""
        return self._configuration

    def copy_base(self, w: UIWidget) -> UIWidget:
        """Copy private properties of base class."""
        w._position = self._position
        w._size = self._size
        w._associated_filters = self._associated_filters.copy()
        w._configuration = self._configuration.copy()
        return w

    @abstractmethod
    def copy(self, new_parent: UIPage) -> UIWidget:
        """Copy the object.

        This method needs to perform a deep copy of the object, excluding generatable state, such as the widgets.

        Args:
            new_parent: The parent of the copy.

        """
        raise NotImplementedError

    @abstractmethod
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        """Get the configuration widget.

        This method shall return a widget that will be placed within the configuration dialog.
        """
        # TODO warum nutzt nur eine der implementierenden klassen überhaupt das parent objekt?
        raise NotImplementedError

    def get_variante(self) -> str:
        """Get the filter variant.

        This method needs to be overridden if there are multiple fitting widgets for a filter
        type in order for the show file saving (and loading) to choose the correct one.
        """
        return ""

    def push_update(self) -> None:
        """Use this method to trigger a filter update process."""
        # TODO ensure that this honors ready wait
        filter_ids = self.filter_ids
        for entry in self.generate_update_content():
            k = entry[0]
            v = entry[1]
            if ":" in k:
                split_key = k.split(":")
                target_fid = split_key[0]
                k = split_key[1]
            else:
                if not filter_ids:
                    continue
                target_fid = filter_ids[0]
            self._network_manager.send_gui_update_to_fish(self.parent.scene.scene_id, target_fid, k, v)

    def close(self) -> None:
        """Implement this method to react on the widget being removed from the widget holder."""
        return  # Implementing this is optional


class FilterUpdateCallbackMixin(ABC):
    """Mixin for UI widgets that listen to fish updates of their linked filter.

    Classes using this mixin must implement the abstract ``_update_from_fish`` method and are responsible
    for calling ``_register_fish_callback`` once the linked filter has been set.

    The callback registration lives as long as the widget model itself and is removed by ``close`` once
    the widget is removed from its page. Player pages may construct and destroy Qt views of the same
    widget model at any time, so ``_update_from_fish`` implementations must tolerate their Qt views
    being already destroyed.
    """

    _registered_callback_key: tuple[Scene, str] | None = None

    def _register_fish_callback(self, f: Filter | None) -> None:
        """Register the fish update callback for the given filter, re-registering it upon filter changes.

        Registering is skipped if the callback is already registered for the given filter.

        Args:
            f: The filter whose updates the widget wants to receive.

        """
        if f is None:
            raise ValueError("The provided filter was None.")
        new_key = (f.scene, f.filter_id)
        if self._registered_callback_key == new_key:
            return
        self._unregister_fish_callback()
        f.scene.board_configuration.register_filter_update_callback(f.scene, f.filter_id, self._update_from_fish)
        self._registered_callback_key = new_key

    def _unregister_fish_callback(self) -> None:
        """Remove the update callback registered for the linked filter, if any."""
        registered_key = self._registered_callback_key
        if registered_key is None:
            return
        self._registered_callback_key = None
        scene, filter_id = registered_key
        scene.board_configuration.remove_filter_update_callback(scene, filter_id, self._update_from_fish)

    def _handle_filter_id_rename(self, old_id: str, new_id: str) -> None:
        """Move the fish update registration along with a rename of the linked filter.

        Args:
            old_id: The filter id under which the callback is currently registered.
            new_id: The filter id to register the callback for instead.

        """
        registered_key = self._registered_callback_key
        if registered_key is None or registered_key[1] != old_id:
            return
        scene = registered_key[0]
        self._unregister_fish_callback()
        scene.board_configuration.register_filter_update_callback(scene, new_id, self._update_from_fish)
        self._registered_callback_key = (scene, new_id)

    @abstractmethod
    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Handle a fish update parameter for the linked filter.

        Args:
            param: The update parameter sent by fish.

        """
        raise NotImplementedError

    def __del__(self) -> None:
        """Unregister the fish update callback (fallback in case close was not called)."""
        try:
            self._unregister_fish_callback()
        except (RuntimeError, AttributeError):
            pass

    def close(self) -> None:
        """Unregister the fish update callback as this widget is being removed.

        Subclasses overriding this method must call ``super().close()`` so that the fish update
        registration is removed as well.
        """
        self._unregister_fish_callback()


class UIPage:
    """Show UI Page.

    This class represents a page containing widgets that can be used to control the show.
    """

    def __init__(self, parent: Scene) -> None:
        """Construct a UI Page.

        Arguments:
            parent: The parent Scene.

        """
        self._widgets: list[UIWidget] = []
        self._parent_scene: Scene = parent
        self._title: str = ""
        self._player: str | None = None
        self.display_update_required = False

    @property
    def scene(self) -> Scene:
        """Get the scene this page is bound to."""
        return self._parent_scene

    @property
    def page_active_on_player(self) -> bool:
        """Returns true if this page is currently displayed on any player."""
        return self._player is not None

    def activate_on_player(self, player: str) -> None:
        """Set the player this page is displayed on."""
        self._player = player
        # TODO push page to player

    @property
    def widgets(self) -> list[UIWidget]:
        """Returns a copy of the internal widget list."""
        return list(self._widgets)

    @property
    def title(self) -> str:
        """Get or set page title."""
        return self._title

    @title.setter
    def title(self, new_title: str) -> None:
        self._title = new_title

    def copy(self, new_parent: Scene) -> UIPage:
        """Copy the page."""
        new_page = UIPage(new_parent)
        new_page._player = self._player
        new_page._title = self._title
        for w in self._widgets:
            new_page._widgets.append(w.copy(new_page))
        return new_page

    def append_widget(self, widget: UIWidget) -> None:
        """Add a widget to the page."""
        self._widgets.append(widget)

    def push_update(self) -> None:
        """Indicate that updates to the running filters should be sent."""

    def remove_widget(self, widget: UIWidget) -> None:
        """Remove a widget from the page."""
        self._widgets.remove(widget)


class ShowUI:
    """Container class containing all pages of the show.

    The _page_storage variable contains the pages per scene.
    """

    _fish_connector: NetworkManager | None = None

    def __init__(self) -> None:
        """Initialize the show UI.

        At any given time there may only be one instance of this class running in the player but one might construct
        arbitrary amounts for editing purposes.
        """
        # List of scene tuples. A scene tuple consists out of the scene name and a list of associated UI pages.
        self._page_storage: list[tuple[str, list[UIPage]]] = []
        self._active_scene: int = 0

    @property
    def active_scene(self) -> int:
        """Get the index of the current active scene."""
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
        """Get all scene names."""
        scene_name_list = []
        for scene_name, _ in self._page_storage:
            scene_name_list.append(scene_name)
        return scene_name_list

    @property
    def pages(self) -> list[UIPage]:
        """Enumerate all UI pages.

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
