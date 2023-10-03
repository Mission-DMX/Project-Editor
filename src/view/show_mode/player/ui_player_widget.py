from PySide6.QtWidgets import QWidget, QGridLayout

from model import Scene
from view.show_mode.editor.editor_tab_widgets.scene_ui_page_editor_widget import UIWidgetHolder


class UIPlayerWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._scene: Scene | None = None
        self.setLayout(QGridLayout(self))
        self._widgets: list[UIWidgetHolder] = []
        self._ui_page_window_index: int = 0

    @property
    def scene(self) -> Scene | None:
        return self._scene

    @scene.setter
    def scene(self, new_scene: Scene):
        #if self._scene:
        #    for w in self._widgets:
        #        w.unregister()
        #    self._widgets.clear()
        self._scene = new_scene
        if new_scene:
            if self._ui_page_window_index < len(new_scene.ui_pages):
                for uiw in new_scene.ui_pages[self._ui_page_window_index].widgets:
                    widget = UIWidgetHolder(uiw, self, False)
                    self._widgets.append(widget)
