# coding=utf-8
"""Module for filter settings editor"""
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLineEdit, QLabel, QPushButton, QGraphicsItem, QDialog, QFormLayout
from PySide6.QtSvgWidgets import QGraphicsSvgItem

from model import Filter
from view.show_mode.node_editor_widgets.column_select import ColumnSelect
from view.show_mode.node_editor_widgets.cue_editor import CueEditor


class FilterSettingsItem(QGraphicsSvgItem):
    """GraphicsItem to handle opening filter settings dialog.
    
    Attributes:
        filter: The filter this item belongs to
    """

    def __init__(self, filter_: Filter, parent: QGraphicsItem):
        super().__init__("src/resources/settings.svg", parent)
        self.filter = filter_
        self.on_update = lambda: None
        self.setScale(0.2)
        self.moveBy(parent.boundingRect().width() / 2, parent.boundingRect().height() - 20)

    def focusOutEvent(self, ev):
        """
        Override to handle buggy behaviour
        Args:
            ev: event
        """
        super().focusOutEvent(ev)
        if self.on_update is not None:
            self.on_update()

    def keyPressEvent(self, ev):
        """
        Override to handle buggy behaviour
        Args:
            ev: event
        """
        if ev.key() == Qt.Key.Key_Enter or ev.key() == Qt.Key.Key_Return:
            if self.on_update is not None:
                self.on_update()
                return
        super().keyPressEvent(ev)

    def mousePressEvent(self, ev):
        """Handle left mouse button click by opening filter settings dialog"""
        if ev.button() == Qt.MouseButton.LeftButton:
            FilterSettingsDialog(self.filter).exec()


def check_if_filter_has_special_widget(filter_):
    if 39 <= filter_.filter_type <= 43:
        return ColumnSelect()
    elif filter_.filter_type == 44:
        return CueEditor()
    else:
        return None


class FilterSettingsDialog(QDialog):
    """
    
    Attributes:
        filter: The filter whose settings this dialog displays
    """

    def __init__(self, filter_: Filter) -> None:
        super().__init__()
        self.filter = filter_
        self.setWindowTitle("Filter Settings")
        # Form layout:
        # Initial Parameters
        # ip1_name: ip1_value_editable
        # ip2_name: ip2_value_editable
        # Filter Configurations
        # fc1_name: fc1_value_editable
        # fc2_name: fc2_value_editable
        layout = QFormLayout()
        # Function pointer to handle patching information. Only set, when filter is universe filter

        self._special_widget = check_if_filter_has_special_widget(filter_)
        if self._special_widget:
            self._special_widget.configuration = filter_.filter_configurations
            self._special_widget.parameters = filter_.initial_parameters
            layout.addRow("", self._special_widget.get_widget())
        else:
            add_patch_info: bool = filter_.filter_type == 11
            # Only add initial parameters section if present
            if len(filter_.initial_parameters) > 0:
                layout.addRow("Initial Parameters", QLabel(""))
                for key, value in filter_.initial_parameters.items():
                    line_edit = QLineEdit()
                    line_edit.setText(value)
                    line_edit.textChanged.connect(lambda new_value: self._ip_value_changed(key, new_value))
                    layout.addRow(key, line_edit)
            # Only add filter configuration section if present
            if len(filter_.filter_configurations) > 0:
                layout.addRow("Filter Configurations", QLabel(""))
                for key, value in filter_.filter_configurations.items():
                    line_edit = QLineEdit()
                    line_edit.setText(value)
                    line_edit.textChanged.connect(lambda new_value: self._fc_value_changed(key, new_value))
                    if add_patch_info:
                        key = self._add_patch_info(key, value)
                    layout.addRow(key, line_edit)
        self._ok_button = QPushButton("Ok")
        self._ok_button.pressed.connect(self.ok_button_pressed)

        layout.addRow("", self._ok_button)

        self.setLayout(layout)

    def _add_patch_info(self, key: str, value: str) -> str:
        if self.filter._filter_type != 11:
            return key
        # Only channel inputs have patching info
        if key == "universe":
            return key
        # Fetch universe
        universe_id = int(self.filter.filter_configurations["universe"])
        for uni in self.filter.board_configuration.universes:
            if uni.universe_proto.id == universe_id:
                universe = uni
                break
        else:
            logging.warning("Could not find universe %s", universe_id)
            return key
        # Fetch patching short name
        for channel in universe.patching:
            if channel.address == int(value):
                key = f"{key} : {channel.fixture.short_name}"
        return key

    def _ip_value_changed(self, key, value):
        self.filter.initial_parameters[key] = value

    def _fc_value_changed(self, key, value):
        self.filter.filter_configurations[key] = value

    def ok_button_pressed(self):
        if self._special_widget:
            for k in self._special_widget.configuration.keys():
                self.filter.filter_configurations[k] = self._special_widget.configuration[k]
            for k in self._special_widget.parameters.keys():
                self.filter.initial_parameters[k] = self._special_widget.parameters[k]
        self.close()
