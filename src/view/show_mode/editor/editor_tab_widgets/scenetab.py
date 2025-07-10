"""Widget containing a nodeeditor for one scene."""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QVBoxLayout, QWidget

from model import Scene
from model.scene import FilterPage
from view.show_mode.editor.nodeeditor import NodeEditorWidget


class SceneTabWidget(QWidget):
    """Widget representing a scene as a tab page"""

    def __init__(self, scene: Scene | FilterPage) -> None:
        super().__init__()
        self._scene = scene
        self._layout = QVBoxLayout()

        self._toolbar = QToolBar(self)
        self._add_filter_action = QAction("Add Filter")
        self._add_filter_action.setEnabled(False)  # TODO implement behaviour (for touch screen use)
        self._toolbar.addAction(self._add_filter_action)
        self._layout.addWidget(self._toolbar)
        self._node_editor_widget = NodeEditorWidget(scene, self)
        self._layout.addWidget(self._node_editor_widget)
        self.setLayout(self._layout)
        # self._scene_ui_editor_widget = SceneUIManagerWidget(scene, self)
        # self.addTab(self._scene_ui_editor_widget, "Scene UI Editor")

    @property
    def scene(self) -> Scene:
        """The scene the tab represents"""
        if isinstance(self._scene, Scene):
            return self._scene

        return self._scene.parent_scene

    @property
    def filter_page(self) -> Scene:
        return self._scene

    def refresh(self) -> None:
        self._node_editor_widget.refresh()
