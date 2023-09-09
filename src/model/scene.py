# coding=utf-8
"""Scene module"""
from typing import TYPE_CHECKING
from .filter import Filter

if TYPE_CHECKING:
    from .board_configuration import BoardConfiguration


class Scene:
    """Scene for show file."""

    def __init__(self, scene_id: int,
                 human_readable_name: str,
                 board_configuration: "BoardConfiguration"):
        self._scene_id: int = scene_id
        self._human_readable_name: str = human_readable_name
        self._board_configuration: "BoardConfiguration" = board_configuration
        self._filters: list[Filter] = []
        self._filter_pages = []

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
