# coding=utf-8
"""Widget containing a nodeeditor for one scene."""
from PySide6.QtWidgets import QWidget, QTabWidget, QPushButton, QGridLayout

from model import Scene
from model.scene import FilterPage
from view.show_mode.editor.nodeeditor import NodeEditorWidget
from view.show_mode.editor.scene_editor import SceneManagerWidget


class SceneTabWidget(QTabWidget):
    """Widget representing a scene as a tab page"""

    def __init__(self, scene: Scene | FilterPage):
        super().__init__()
        self._scene = scene

        self.setTabPosition(QTabWidget.TabPosition.West)

        self._node_editor_widget = NodeEditorWidget(scene, self)
        self.addTab(self._node_editor_widget, "Filter Editor")
        self._scene_ui_editor_widget = SceneManagerWidget(scene, self)
        self.addTab(self._scene_ui_editor_widget, "Scene UI Editor")

    @property
    def scene(self) -> Scene:
        """The scene the tab represents"""
        if isinstance(self._scene, Scene):
            return self._scene
        else:
            return self._scene.parent_scene

    @property
    def filter_page(self):
        return self._scene

    def refresh(self):
        self._node_editor_widget.refresh()
