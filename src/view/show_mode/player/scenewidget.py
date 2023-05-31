# coding=utf-8
"""Scene widget for scene player"""
from PySide6.QtWidgets import QWidget, QPushButton

from model import Scene
from file.write import create_xml


class SceneWidget(QPushButton):
    """Widget to be displayed for a scene in the show player"""
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
        xml = create_xml(self._scene.board_configuration)
        self._scene.board_configuration.broadcaster.load_show_file.emit(xml, False)
        self._scene.board_configuration.broadcaster.change_active_scene.emit(self._scene.scene_id)

    @property
    def scene(self) -> Scene:
        """The scene this widget represents"""
        return self._scene