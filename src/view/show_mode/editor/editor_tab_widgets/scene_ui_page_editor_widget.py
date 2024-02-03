# coding=utf-8
"""A scene can have multiple pages"""
import logging

from PySide6.QtWidgets import QWidget, QMenu, QGridLayout, QPushButton, QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint, Signal, QSize
from PySide6.QtGui import QMouseEvent, QAction

from model import Scene, Filter, UIPage, UIWidget
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.show_ui_widgets import filter_to_ui_widget
from view.show_mode.editor.show_ui_widgets.autotracker.UIWidget import AutoTrackerUIWidget


class UIWidgetHolder(QWidget):
    """Widget to hold node editor widgets and move them around"""

    closing = Signal()

    def __init__(self, child: UIWidget, parent: QWidget, instance_for_editor: bool = True):
        super().__init__(parent)
        self._model = child
        if instance_for_editor:
            self._child = child.get_configuration_widget(self)
        else:
            self._child = child.get_player_widget(self)
            self._child.setEnabled(True)
            self._child.setVisible(True)
        self._child.setParent(self)
        self._label = QLabel(child.filter_id, self)
        self.update_size()
        if instance_for_editor:
            self._close_button = QPushButton("X", self)
            self._close_button.resize(30, 30)
            self._close_button.move(self.width() - 40, 0)
            self._close_button.clicked.connect(self.close)
            self._edit_button = QPushButton("Edit", self)
            self._edit_button.resize(50, 30)
            self._edit_button.move(0, 0)
            self._edit_button.clicked.connect(self._show_edit_dialog)
        self._old_pos = QPoint()
        if instance_for_editor:
            self.setStyleSheet("border: 1px solid black")
        self.setVisible(True)
        super().move(self._model.position[0], self._model.position[1])
        self._edit_dialog = None

    def update_size(self):
        self.setMinimumWidth(100)
        self.setMinimumHeight(30)

        child_layout = self._child.layout()
        if child_layout:
            minimum_size = child_layout.totalMinimumSize()
        else:
            minimum_size = QSize(250, 100)
        w = max(minimum_size.width() + 50, self.minimumWidth())
        h = max(minimum_size.height() + 50, self.minimumHeight())
        self._label.resize(w, 20)
        self._label.move(10, w - 30)
        self.resize(w, h)
        self.repaint()

    def closeEvent(self, event) -> None:
        """Emits closing signal.

        Args:
            event: The closing event.
        """
        self.closing.emit()
        try:
            self._model.parent.widgets.remove(self._model)
        except ValueError:
            pass
        super().closeEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Saves the current position on left click.

        Args:
            event: The mouse event.
        """
        if event.button() is Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Moves the widget on mouse drag.

        Args:
            event: The mouse event.
        """
        # offset = QPoint(event.globalPos() - self._old_pos)
        self.move(self.parent().mapFromGlobal(event.globalPos()))
        # self.move(self.x() + offset.x(), self.y() + offset.y())
        self._old_pos = event.globalPos()

    @property
    def holding(self) -> NodeEditorFilterConfigWidget:
        """The widget the holder is holding"""
        return self._child

    def move(self, new_pos: QPoint):
        super().move(new_pos)
        self._model.position = (new_pos.x(), new_pos.y())

    def _show_edit_dialog(self):
        if not self._edit_dialog:
            self._edit_dialog = QDialog(self)
            layout = QVBoxLayout()
            layout.addWidget(self._model.get_config_dialog_widget(self._edit_dialog))
            # TODO add cancel and close buttons
            self._edit_dialog.setLayout(layout)
        self._edit_dialog.show()

    def unregister(self):
        # setting the parent to None is required!
        self._child.setParent(None)
        self._child.setVisible(False)
        self._child.setEnabled(False)


class SceneUIPageEditorWidget(QWidget):
    """This class represents a part of a scene"""

    def __init__(self, page: UIPage, parent: QWidget) -> None:
        super().__init__(parent)
        self._ui_page: UIPage = page
        self.setLayout(QGridLayout(self))
        self._widgets: list[UIWidgetHolder] = []
        for uiw in self._ui_page.widgets:
            widget = UIWidgetHolder(uiw, self)
            self._widgets.append(widget)
            widget.closing.connect(lambda: self._widgets.remove(widget))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() is Qt.MouseButton.RightButton:
            self._widget_selection_menu(event.pos())

    def _widget_selection_menu(self, pos: QPoint):
        menu = QMenu(self)
        added_filters = 0
        for filter_ in self.ui_page.scene.filters:
            if len(filter_.gui_update_keys.keys()) < 1:
                continue
            action = QAction(filter_.filter_id, self)
            menu.addAction(action)
            action.triggered.connect(lambda checked=False, filter__=filter_: self._add_filter_widget(filter__, pos))
            added_filters += 1
        if added_filters == 0:
            action = QAction("There are no suitable filters in the scene", menu)
            action.setEnabled(False)
            menu.addAction(action)
        menu.addSeparator()
        auto_track_action = QAction("Auto Tracker", self)
        auto_track_action.triggered.connect(lambda checked=False, filter__=None: self._add_generic_widget(
            AutoTrackerUIWidget("", self._ui_page), pos)
        )
        menu.addAction(auto_track_action)
        menu.popup(self.mapToGlobal(pos))

    def _add_filter_widget(self, filter_: Filter, pos: QPoint):
        """Adds the filter widget to the page at the specified position.

        Args:
            ui_widget: A widget to manage a filter
            pos: The position at which the widget should be placed
        """
        # TODO replace with filter.gui_update_keys to ui widget / Change function to construct one from the keys
        config_widget = filter_to_ui_widget(filter_, self._ui_page)
        self._add_generic_widget(config_widget, pos)

    def _add_generic_widget(self, config_widget: UIWidget, pos: QPoint):
        widget = UIWidgetHolder(config_widget, self)
        # widget.holding.parameters = filter_.initial_parameters
        # widget.holding.configuration = filter_.filter_configurations
        self._widgets.append(widget)
        widget.closing.connect(lambda: self._widgets.remove(widget))
        widget.move(pos)
        self._ui_page.append_widget(config_widget)


    @property
    def ui_page(self) -> UIPage:
        """The scene the page represents"""
        return self._ui_page

    @property
    def filter_widgets(self) -> list[NodeEditorFilterConfigWidget]:
        """List of all the filter widgets currently displayed on the page"""
        return self._widgets
