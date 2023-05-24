# coding=utf-8
"""Scene widget for scene player"""
from PySide6.QtWidgets import QWidget, QPushButton

from model import Scene


class SceneWidget(QPushButton):
    """Widget to be displayed for a scene in the show player"""
    width = 50
    height = 25

    def __init__(self, scene: Scene, parent: QWidget = None):
        super().__init__(parent)
        self._scene = scene
        self.clicked.connect(self._scene)

    def _clicked(self):
        """Handles behaviour when scene button was clicked"""
        print(f"Play scene {self._scene.scene_id}")
