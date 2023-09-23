# coding=utf-8
"""Widget containing a nodeeditor for one scene."""
from PySide6.QtWidgets import QWidget, QTabWidget, QTabBar, QGridLayout, QDialog

from model import Scene
from .scene_filter_page_widget import ScenePageWidget


class SceneManagerWidget(QTabWidget):
    """Widget containing the scene pages"""

    def __init__(self, scene: Scene, parent: QWidget):
        super().__init__(parent)
        self._scene = scene
        self.setTabsClosable(True)

        self.addTab(QWidget(), "+")
        self.tabBar().tabButton(self.count() - 1, QTabBar.ButtonPosition.RightSide).hide()

        self._poped_pages: list[QDialog] = []
        self._nodeeditor_dialog = None

        self._add_page()

        self.tabBarClicked.connect(self._tab_bar_clicked)
        self.tabCloseRequested.connect(self.removeTab)
        self.tabBarDoubleClicked.connect(self._pop_page)

    def _tab_bar_clicked(self, index: int):
        """Handles behaviour when +/- button was clicked"""
        if index == self.count() - 1:
            self._add_page()

    def _add_page(self):
        """Adds a page to the scene"""
        page_widget = ScenePageWidget(self._scene, self)
        self.insertTab(self.count() - 1, page_widget, f"Page {self.count()}")
        self.setCurrentWidget(page_widget)

    def _pop_page(self, index: int) -> QDialog:
        """Displays the given page in a new window.

        Args:
            index: The index of the tab in the tab bar.
        """
        if index == self.count() - 1:
            return
        page = self.widget(index)
        dialog = QDialog()
        layout = QGridLayout()
        layout.addWidget(page)
        dialog.setLayout(layout)
        dialog.finished.connect(lambda: self._unpop_page(page, index))
        self._poped_pages.append(dialog)
        dialog.show()

    def _unpop_page(self, page: QWidget, index: int):
        """Reinserts page.

        Args:
            page: Page to be reinserted.
            index: Position in the tab bar.
        """
        self.insertTab(index, page, f"Page {index + 1}")

    @property
    def scene(self):
        """The scene managed by the scene manager"""
        return self._scene
