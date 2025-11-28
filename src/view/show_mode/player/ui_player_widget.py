"""Qt widget to display show UI widgets."""

from typing import override

from PySide6.QtCore import QPoint, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QComboBox, QGridLayout, QWidget

from model import Broadcaster, Scene
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor.scene_ui_page_editor_widget import UIWidgetHolder


class UIPlayerWidget(QWidget):
    """Container for Show UI widgets to be used in the UI page player."""

    selected_page_changed = Signal(int)
    """Signal gets emitted, when user changes selected UI page."""

    def __init__(self, parent: QWidget) -> None:
        """UI container widget.

        Args:
            parent: The parent Qt widget.

        """
        super().__init__(parent)
        self._scene: Scene | None = None
        self.setLayout(QGridLayout(self))
        self._widgets: list[UIWidgetHolder] = []
        self._ui_page_window_index: int = 0
        self._page_combo_box = QComboBox(self)
        self._page_combo_box.setEditable(False)
        self._page_combo_box.setFixedSize(130, 25)
        self._page_combo_box.pos = QPoint(10, self.height() - 35)
        self._page_combo_box.show()
        self._page_combo_box.currentIndexChanged.connect(self._switch_page_index)
        b = Broadcaster()
        b.view_to_show_player.connect(self.check_page_update)
        b.uipage_renamed.connect(self._page_renamed)
        self.selected_page_changed_locked: bool = False

    @override
    def resizeEvent(self, event: QResizeEvent, /) -> None:
        super().resizeEvent(event)
        self._page_combo_box.pos = QPoint(10, self.height() - 35)

    @property
    def scene(self) -> Scene | None:
        """Get or set the associated scene."""
        return self._scene

    @scene.setter
    def scene(self, new_scene: Scene | None) -> None:
        self._scene = new_scene
        self._update_page_cb()
        self._update_page()

    def _update_page_cb(self) -> None:
        self._page_combo_box.clear()
        if self._scene is None:
            return

        for i, page in enumerate(self._scene.ui_pages):
            self._page_combo_box.addItem(f"[{i + 1}] {page.title}", i)

    def _update_page(self) -> None:
        for w in self._widgets:
            w.unregister()
            w.setParent(None)
            w.deleteLater()
        self._widgets.clear()
        scene = self._scene
        if scene is None:
            return
        if self._ui_page_window_index < len(scene.ui_pages):
            for uiw in scene.ui_pages[self._ui_page_window_index].widgets:
                widget = UIWidgetHolder(uiw, self, False)
                self._widgets.append(widget)
        else:
            self._ui_page_window_index = max(len(scene.ui_pages) - 1, 0)

    def check_page_update(self) -> None:
        """Perform a check if anything (including dimensions) need to be changed."""
        if self._scene is None:
            return
        index = self._ui_page_window_index
        if index >= len(self._scene.ui_pages) or index < 0:
            return
        page = self._scene.ui_pages[index]
        if page.display_update_required:
            self._update_page()
            page.display_update_required = False

    def _switch_page_index(self) -> None:
        self._ui_page_window_index = self._page_combo_box.currentData()
        if self._ui_page_window_index is None:
            self._ui_page_window_index = 0
        self._update_page()
        if not self.selected_page_changed_locked:
            self.selected_page_changed.emit(self._ui_page_window_index)

    def goto_page(self, new_index: int) -> None:
        """Select a specific UI page by its index.

        Args:
            new_index: The index of the UI page to select.
        """
        self._page_combo_box.setCurrentIndex(new_index)

    def _page_renamed(self, scene_id: int) -> None:
        if self._scene is None:
            return
        if scene_id == self._scene.scene_id:
            self._update_page_cb()
