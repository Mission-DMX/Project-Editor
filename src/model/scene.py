# coding=utf-8
"""Scene module"""
from typing import TYPE_CHECKING
from .filter import Filter

if TYPE_CHECKING:
    from .board_configuration import BoardConfiguration


class FilterPage:
    def __init__(self):
        self._filters: list[Filter] = []
        self._child_pages: list["FilterPage"] = []
        self._name: str = ""

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        self._name = str(new_name)

    @property
    def filters(self) -> list[Filter]:
        return self._filters

    @property
    def child_pages(self) -> list["FilterPage"]:
        return self._child_pages


class Scene:
    """Scene for show file."""

    def __init__(self, scene_id: int,
                 human_readable_name: str,
                 board_configuration: "BoardConfiguration"):
        self._scene_id: int = scene_id
        self._human_readable_name: str = human_readable_name
        self._board_configuration: "BoardConfiguration" = board_configuration
        self._filters: list[Filter] = []
        self._filter_pages: list[FilterPage] = []

    @property
    def scene_id(self) -> int:
        """The unique id of the scene"""
        return self._scene_id

    @property
    def human_readable_name(self) -> str:
        """The human readable name of the scene displayed by the ui"""
        return self._human_readable_name

    @human_readable_name.setter
    def human_readable_name(self, human_readable_name: str):
        """Sets the human readable name of the scene displayed by the ui"""
        self._human_readable_name = human_readable_name

    @property
    def board_configuration(self) -> "BoardConfiguration":
        """The board configuration the scene is part of"""
        return self._board_configuration

    @property
    def filters(self) -> list[Filter]:
        """The filters of the scene"""
        return self._filters

    @property
    def pages(self) -> list[FilterPage]:
        """Returns the associated list of filter pages"""
        if len(self._filter_pages) == 0:
            default_page = FilterPage()
            default_page.name = "default"
            for f in self._filters:
                default_page.filters.append(f)
            self._filter_pages.append(default_page)
        return self._filter_pages
