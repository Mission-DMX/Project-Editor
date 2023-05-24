# coding=utf-8
"""Show player to remote control fish show mode"""
from PySide6.QtWidgets import QWidget

from model import BoardConfiguration


class ShowPlayerWidget(QWidget):
    """Widget to remote control fish show mode"""
    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget = None):
        super().__init__(parent)
        self._board_configuration = board_configuration
