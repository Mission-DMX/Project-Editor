# coding=utf-8
"""Widget containing a nodeeditor for one scene."""
import logging

from PySide6.QtWidgets import QWidget, QTabWidget, QTabBar, QPushButton, QGridLayout, QMainWindow
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCloseEvent

from src.model import Scene
from .nodeeditor import NodeEditorDialog
from .scenepage import ScenePageWidget


class SceneTabWidget(QWidget):
    """Widget representing a scene as a tab page"""

    def __init__(self, scene: Scene):
        super().__init__()
        self._scene = scene

        self._scenemanager = SceneManagerWidget(scene, self)
        self._nodeeditor = NodeEditorDialog(scene)

        self._open_nodeeditor_btn = QPushButton("Node Editor", self)
        self._open_nodeeditor_btn.clicked.connect(self._nodeeditor.exec)

        layout = QGridLayout(self)
        layout.addWidget(self._scenemanager, 0, 0)
        layout.addWidget(self._open_nodeeditor_btn, 1, 0)
        self.setLayout(layout)

    @property
    def scene(self) -> Scene:
        return self._scene


class SceneManagerWidget(QTabWidget):
    """Widget containing the scene pages"""

    def __init__(self, scene: Scene, parent: QWidget):
        super().__init__(parent)
        self._scene = scene
        self.setTabsClosable(True)

        self.addTab(QWidget(), "+")
        self.tabBar().tabButton(self.count() - 1, QTabBar.ButtonPosition.RightSide).hide()

        self._poped_pages: list[QMainWindow] = []

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

    def _pop_page(self, index: int):
        """Displays the given page in a new window.

        Args:
            index: The index of the tab in the tab bar.
        """
        if index == self.count() - 1:
            return
        page = self.widget(index)
        window = PageWindow()
        layout = QGridLayout()
        layout.addWidget(page)
        window.setLayout(layout)
        window.closing.connect(lambda: self._unpop_page(page, index))
        self._poped_pages.append(window)
        window.show()

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


class PageWindow(QMainWindow):
    """Extends QMainWindow by adding closing signal"""

    closing = Signal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closing.emit()
