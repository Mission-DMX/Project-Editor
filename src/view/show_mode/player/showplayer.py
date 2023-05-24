# coding=utf-8
"""Show player to remote control fish show mode"""
from PySide6.QtWidgets import QWidget, QGridLayout

from model import BoardConfiguration
from .scenewidget import SceneWidget


class ShowPlayerWidget(QWidget):
    """Widget to remote control fish show mode"""

    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget = None):
        super().__init__(parent)
        self._board_configuration = board_configuration
        layout = QGridLayout(self)
        scene_amount = len(self._board_configuration.scenes)
        max_columns = int(self.width() / SceneWidget.width)
        max_rows = int(self.height() / SceneWidget.height)
        columns = scene_amount / max_rows
