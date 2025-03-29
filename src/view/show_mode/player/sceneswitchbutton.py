# coding=utf-8
"""Scene widget for scene player"""
from PySide6.QtWidgets import QPushButton, QWidget

from model import Scene


class SceneSwitchButton(QPushButton):
    """Widget to be displayed for a scene in the show player.
    Clicking the button will transmit the board config to fish and change the active scene.
    """
    width = 100
    height = 75

    def __init__(self, scene: Scene, parent: QWidget = None):
        super().__init__(parent)
        self._scene = scene
        self.clicked.connect(self._clicked)
        self.setFixedSize(self.width, self.height)
        self.setText(self._scene.human_readable_name)

    def _clicked(self):
        """Handles behaviour when scene button was clicked"""
        # transmit_to_fish(self._scene.board_configuration)
        self._scene.board_configuration.broadcaster.change_active_scene.emit(self._scene)

    @property
    def scene(self) -> Scene:
        """The scene this widget represents"""
        return self._scene
