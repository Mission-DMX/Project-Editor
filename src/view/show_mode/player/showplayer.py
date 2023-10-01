# coding=utf-8
"""Show player to remote control fish show mode"""
from PySide6.QtWidgets import QWidget, QGridLayout

from model import BoardConfiguration, Scene
from .scenetransmitbutton import SceneTransmitButton


class _PlaceholderWidget(QWidget):
    """Placeholder for grid"""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(SceneTransmitButton.width, SceneTransmitButton.height)


class ShowPlayerWidget(QWidget):
    """Widget to remote control fish show mode"""

    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget = None):
        super().__init__(parent)
        self._board_configuration = board_configuration

        self._max_columns = 10  # int(self.width() / SceneWidget.width)
        self._max_rows = 10  # int(self.height() / SceneWidget.height)

        self._grid: list[SceneTransmitButton] = []

        self._board_configuration.broadcaster.scene_created.connect(self._add_scene)
        self._board_configuration.broadcaster.delete_scene.connect(self._remove_scene)
        # TODO add UIPage player

    def _index_to_position(self, index: int) -> tuple[int, int]:
        """Calculates the grid position from index.

        Args:
            index: The index

        Returns:
            A tuple of x-y coordinates (column, row)
        """
        column = int(index / self._max_rows)
        row = index - column * self._max_rows
        return column, row

    def _add_scene(self, scene: Scene):
        """Adds a scene to the player.

        Args:
            scene: Scene to be added.
        """
        scene_widget = SceneTransmitButton(scene, self)
        self._grid.append(scene_widget)
        self._reload()

    def _remove_scene(self, scene: Scene):
        """Removes a scene from the player.

        Args:
            scene: Scene to be removed.
        """
        for scene_widget in self._grid:
            if scene_widget.scene.scene_id is scene.scene_id:
                self._grid.remove(scene_widget)
                scene_widget.deleteLater()
                self._reload()
                break

    def _reload(self):
        """Reloads all scene widgets by filling up emtpty spaces"""
        index = 0
        for scene_widget in self._grid:
            column, row = self._index_to_position(index)
            scene_widget.move(column * scene_widget.width + 5, row * scene_widget.height + 5)
            index += 1
