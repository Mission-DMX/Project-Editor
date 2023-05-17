from abc import ABC, abstractmethod

from Network import NetworkManager


class UIWidget(ABC):
    """This class represents a link between an interactable widget on a page and the corresponding filter."""

    def __init__(self, fid: str, parent_page: UIPage):
        """ Set up the basic components of a widget.

        Arguments:
            fid -- The id of the corresponding filter.
        """
        self._position: tuple[int, int] = (0, 0)
        self._filter_id: str = fid
        self._parent = parent_page

    @abstractmethod
    def generate_update_content(self) -> list[tuple[str, str]]:
        """This method needs to be implemented in order to compute the update content.

        Returns:
            A list of key-value-tuples where each tuple defines a parameter of the filter to be updated.
        """
        raise NotImplementedError

    @property
    def filter_id(self) -> str:
        """Get the id of the linked filter"""
        return self._filter_id

    @property
    def parent(self) -> UIPage:
        """Get the parent page of this widget"""
        return self._parent

    @property
    def position(self) -> tuple[int, int]:
        """Get the position of the widget on the UI page"""
        return self._position

    @position.setter
    def position(self, new_position: tuple[int, int]):
        """Update the position of the widget on the UI page"""
        self._position = new_position
        # TODO notify player about UI update if running


class UIPage:
    """This class represents a page containing widgets that can be used to control the show."""

    def __init__(self, sid: int):
        """Construct a UI Page

        Arguments:
            sid -- The id of the scene where the corresponding filter is located.
        """
        self._widgets: list[UIWidget] = []
        self._scene_id: int = sid
        self._player = None

    @property
    def scene_id(self) -> int:
        """Get the scene this page is bound to"""
        return self._scene_id

    @property
    def page_active_on_player(self) -> bool:
        """Returns true if this page is currently displayed on any player"""
        return self._player is not None

    def activate_on_player(self, player):
        """Set the player this page is displayed on"""
        self._player = player
        # TODO push page to player


class ShowUI:
    """This class contains all pages of the show

    The _page_storage variable contains the pages per scene.
    """
    _fish_connector: NetworkManager = None

    def __init__(self):
        """This constructor initializes the show UI.

        At any given time there may only be one instance of this class running in the player but one might construct
        arbitrary amounts for editing purposes.
        """
        self._page_storage: list[list[UIPage]] = []
        self._active_scene: int = 0

    @property
    def active_scene(self) -> int:
        """Get the index of the current active scene"""
        return self._active_scene

    @active_scene.setter
    def active_scene(self, scene: int):
        """Set the current active scene.

        Warning: setting this property will actually update the current active scene, if this UI is the active one.
        """
        if scene < 0 or scene >= len(self._page_storage):
            raise ValueError("Scene index out of range")
        self._active_scene = scene
        # TODO change scene if active show running
        # TODO notify player about UI update, distribute pages to available players.

    @staticmethod
    @property
    def network_connection() -> NetworkManager:
        """Get the linked network manager"""
        return ShowUI._fish_connector

    @staticmethod
    @network_connection.setter
    def network_connection(self, fish_connector: NetworkManager):
        """Set the linked network manager"""
        ShowUI._fish_connector = fish_connector
