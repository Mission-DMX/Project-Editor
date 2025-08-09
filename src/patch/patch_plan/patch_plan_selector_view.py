"""Selector for Patching witch holds all Patching Universes."""

from __future__ import annotations

from functools import partial
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from PySide6.QtGui import QContextMenuEvent
    from PySide6.QtWidgets import QStackedWidget

logger = getLogger(__name__)


class PatchPlanSelectorView(QtWidgets.QTabWidget):
    """Selector for Patching witch holds all Patching Universes."""

    generate_universe = QtCore.Signal()
    rename_universe = QtCore.Signal(int)
    delete_universe_index = QtCore.Signal(int)

    def __init__(self, parent: QStackedWidget) -> None:
        """Selector for Patching witch holds all Patching Universes."""
        super().__init__(parent=parent)

        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)
        self.addTab(QtWidgets.QWidget(), "+")
        self.tabBarClicked.connect(self._tab_clicked)
        self.tabBar().setCurrentIndex(0)

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Context menu."""
        for index in range(self.tabBar().count() - 1):
            if self.tabBar().tabRect(index).contains(event.pos()):
                menu = QtWidgets.QMenu(self)

                rename_universe = QtGui.QAction("rename Universe", self)
                delete_universe = QtGui.QAction("delete Universe", self)
                rename_universe.triggered.connect(partial(self.rename_universe.emit, index))
                delete_universe.triggered.connect(partial(self.delete_universe_index.emit, index))
                menu.addAction(rename_universe)
                menu.addAction(delete_universe)
                menu.popup(QtGui.QCursor.pos())
                break

    def _tab_clicked(self, scene_index: int) -> None:
        if scene_index == self.tabBar().count() - 1:
            self.generate_universe.emit()
