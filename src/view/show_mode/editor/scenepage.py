# coding=utf-8
"""A scene can have multiple pages"""
import logging

from PySide6.QtWidgets import QWidget, QMenu, QGridLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent, QDragMoveEvent, QAction

from model import Scene, Filter
from .node_editor_widgets import NodeEditorFilterConfigWidget, filter_to_widget


class _WidgetHolder(QWidget):
    """Widget to hold node editor widgets and move them around"""

    def __init__(self, child: NodeEditorFilterConfigWidget, parent: QWidget):
        super().__init__(parent)
        self._child = child
        self.setFixedSize(self._child.get_widget().frameSize())
        self._child.get_widget().setParent(self)
        self._old_pos = QPoint()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() is Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        offset = QPoint(event.globalPos() - self._old_pos)
        self.move(self.x() + offset.x(), self.y() + offset.y())
        self._old_pos = event.globalPos()

    @property
    def holding(self) -> QWidget:
        """The widget the holder is holding"""
        return self._child.get_widget()


class ScenePageWidget(QWidget):
    """This class represents a part of a scene"""

    def __init__(self, scene: Scene, parent: QWidget) -> None:
        super().__init__(parent)
        self._scene = scene
        self.setLayout(QGridLayout(self))
        self._widgets: list[_WidgetHolder] = []

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() is Qt.MouseButton.RightButton:
            self._widget_selection_menu(event.pos())

    def _widget_selection_menu(self, pos: QPoint):
        menu = QMenu(self)
        for filter_ in self._scene.filters:
            action = QAction(filter_.filter_id, self)
            menu.addAction(action)
            action.triggered.connect(lambda checked=False, filter__=filter_: self._add_filter_widget(filter__, pos))
        menu.popup(pos)

    def _add_filter_widget(self, filter_: Filter, pos: QPoint):
        """Adds the filter widget to the page at the specified position.

        Args:
            ui_widget: A widget to manage a filter
            pos: The position at which the widget should be placed
        """
        config_widget = filter_to_widget(filter_)
        widget = _WidgetHolder(config_widget, self)
        self._widgets.append(widget)
        widget.setStyleSheet("border: 1px solid black")
        widget.move(pos)
        widget.setVisible(True)

    @property
    def scene(self) -> Scene:
        """The scene the page represents"""
        return self._scene

    @property
    def filter_widgets(self) -> list[NodeEditorFilterConfigWidget]:
        """List of all the filter widgets currently displayed on the page"""
        return self._widgets
