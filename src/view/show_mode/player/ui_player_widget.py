# coding=utf-8
from PySide6.QtWidgets import QGridLayout, QWidget

from model import Broadcaster, Scene
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor.scene_ui_page_editor_widget import UIWidgetHolder


class UIPlayerWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._scene: Scene | None = None
        self.setLayout(QGridLayout(self))
        self._widgets: list[UIWidgetHolder] = []
        self._ui_page_window_index: int = 0
        Broadcaster().view_to_show_player.connect(self._check_page_update)

    @property
    def scene(self) -> Scene | None:
        return self._scene

    @scene.setter
    def scene(self, new_scene: Scene):
        if self._scene:
            for w in self._widgets:
                w.unregister()
                w.setParent(None)
                w.deleteLater()
            self._widgets.clear()
        self._scene = new_scene
        if new_scene:
            if self._ui_page_window_index < len(new_scene.ui_pages):
                for uiw in new_scene.ui_pages[self._ui_page_window_index].widgets:
                    widget = UIWidgetHolder(uiw, self, False)
                    self._widgets.append(widget)
            else:
                self._ui_page_window_index = max(len(new_scene.ui_pages) - 1, 0)

    def _check_page_update(self):
        if self._scene is None:
            return
        index = self._ui_page_window_index
        if index >= len(self._scene.ui_pages) or index < 0:
            return
        page = self._scene.ui_pages[index]
        if page.display_update_required:
            self.scene = self._scene
            page.display_update_required = False
