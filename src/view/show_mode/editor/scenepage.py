# coding=utf-8
"""A scene can have multiple pages"""
import PySide6.QtGui
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QMouseEvent, QAction

from model import Scene, UIWidget


class ScenePageWidget(QWidget):
    """This class represents a part of a scene"""

    def __init__(self, scene: Scene, parent: QWidget) -> None:
        super().__init__(parent)
        self._scene = scene
        self._ui_widgets: list[UIWidget] = []

    def _add_filter_widget(self, ui_widget: UIWidget, pos: QPointF):
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
            """TODO Implement behaviour when selecting a filter"""
            return

        if event.button() is Qt.MouseButton.RightButton:
            self._widget_selection_menu(event.position())

    def _widget_selection_menu(self, position: QPointF):
        menu = QMenu(self)
        test_action = QAction(text="Test")
        menu.addAction(test_action)
        menu.addAction()
        for filter_ in self._scene.filters:
            pass
        menu.popup(position)

    @property
    def scene(self) -> Scene:
        """The scene the page represents"""
        return self._scene

    @property
    def filter_widgets(self) -> list[UIWidget]:
        """List of all the filter widgets currently displayed on the page"""
        return self._ui_widgets
