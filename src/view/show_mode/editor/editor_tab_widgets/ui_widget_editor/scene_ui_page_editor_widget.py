# coding=utf-8
"""A scene can have multiple pages"""
from typing import Type

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QMouseEvent
from PySide6.QtWidgets import QGridLayout, QMenu, QWidget

from model import Filter, UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor._widget_holder import UIWidgetHolder
from view.show_mode.show_ui_widgets import filter_to_ui_widget, WIDGET_LIBRARY


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

    # TODO add other add method (for example x-touch button opening the dialog in the middle of the editor

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() is Qt.MouseButton.RightButton:
            self._widget_selection_menu(event.pos())

    def _widget_selection_menu(self, pos: QPoint):
        menu = QMenu(self)
        """
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
        """
        for wid, widget_def in WIDGET_LIBRARY:
            action = QAction(widget_def[0], menu)
            action.triggered.connect(lambda checked=False, widget=widget_def: self._add_generic_widget(widget, pos))
            menu.addAction(action)
        menu.popup(self.mapToGlobal(pos))

    def _add_filter_widget(self, filter_: Filter, pos: QPoint):
        """Adds the filter widget to the page at the specified position.

        Args:
            ui_widget: A widget to manage a filter
            pos: The position at which the widget should be placed
        """
        # TODO replace with filter.gui_update_keys to ui widget / Change function to construct one from the keys
        # FIXME we should use this method to provide a context menu to nodes, enabling them to place widgets without
        #  relesecting them.
        config_widget = filter_to_ui_widget(filter_, self._ui_page)
        self._add_generic_widget(config_widget, pos)

    def _add_generic_widget(self, widget_def: tuple[str, Type[UIWidget], list[list[FilterTypeEnumeration]]], pos: QPoint):
        # TODO query filters using filter selection dialog (used from import vfilter), passing the remaining query list
        #  recursively
        config_widget = widget_def[1](self._ui_page)
        widget_holder = UIWidgetHolder(config_widget, self)
        self._widgets.append(widget_holder)
        widget_holder.closing.connect(lambda: self._remove_widget_holder(widget_holder))
        widget_holder.move(pos)
        self._ui_page.append_widget(config_widget)

    def _remove_widget_holder(self, wh: UIWidgetHolder):
        self._widgets.remove(wh)
        self._ui_page.remove_widget(wh.widget)

    @property
    def ui_page(self) -> UIPage:
        """The scene the page represents"""
        return self._ui_page
