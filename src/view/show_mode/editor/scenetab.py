# coding=utf-8
"""Widget containing a nodeeditor for one scene."""
from PySide6.QtWidgets import QWidget, QTabWidget, QPushButton, QGridLayout

from model import Scene
from .nodeeditor import NodeEditorWidget
from .scenemanager import SceneManagerWidget


class SceneTabWidget(QTabWidget):
    """Widget representing a scene as a tab page"""

    def __init__(self, scene: Scene):
        super().__init__()
        self._scene = scene

        self.setTabPosition(QTabWidget.TabPosition.West)

        self.addTab(NodeEditorWidget(scene, self), "Filter Editor")
        self.addTab(SceneManagerWidget(scene, self), "UI Manager")

    @property
    def scene(self) -> Scene:
        """The scene the tab represents"""
        return self._scene
