# coding=utf-8
"""A scene can have multiple pages"""
import logging

from PySide6.QtWidgets import QWidget, QMenu, QGridLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent, QAction

from model import Scene, UIWidget


class ScenePageWidget(QWidget):
    """This class represents a part of a scene"""

    def __init__(self, scene: Scene, parent: QWidget) -> None:
        super().__init__(parent)
        self._scene = scene
        self.setLayout(QGridLayout(self))
        self._ui_widgets: list[UIWidget] = []

    def _add_filter_widget(self, ui_widget: UIWidget, pos: QPoint):
        """Adds the filter widget to the page at the specified position.
        
        Args:
            ui_widget: A widget to manage a filter
            pos: The position at which the widget should be placed
        """
        self._ui_widgets.append(ui_widget)
        widget = ui_widget.get_qt_widget()
        widget.setParent(self)
        widget.move(pos.toPoint())
        widget.setVisible(True)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() is Qt.MouseButton.LeftButton:
            # TODO Implement behaviour when selecting a filter
            return

        if event.button() is Qt.MouseButton.RightButton:
            self._widget_selection_menu(event.position().toPoint())

    def _widget_selection_menu(self, pos: QPoint):
        menu = QMenu(self)
        for filter_ in self._scene.filters:
            action = QAction(filter_.filter_id, self)
            menu.addAction(action)
        menu.popup(pos)

    @property
    def scene(self) -> Scene:
        """The scene the page represents"""
        return self._scene

    @property
    def filter_widgets(self) -> list[UIWidget]:
        """List of all the filter widgets currently displayed on the page"""
        return self._ui_widgets
