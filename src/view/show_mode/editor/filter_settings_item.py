# coding=utf-8
"""Module for filter settings editor"""
from logging import getLogger

import PySide6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QLabel, QPushButton, QGraphicsItem, QDialog, QFormLayout
from PySide6.QtSvgWidgets import QGraphicsSvgItem

from model import Universe
from model.filter import FilterTypeEnumeration, Filter
from .node_editor_widgets import NodeEditorFilterConfigWidget
from .node_editor_widgets.autotracker_settings import AutotrackerSettingsWidget
from .node_editor_widgets.column_select import ColumnSelect
from view.show_mode.editor.node_editor_widgets.cue_editor import CueEditor
from .node_editor_widgets.lua_widget import LuaScriptConfigWidget
from ..effect_stacks.filter_config_widget import EffectsStackFilterConfigWidget

logger = getLogger(__name__)


class FilterSettingsItem(QGraphicsSvgItem):
    """GraphicsItem to handle opening filter settings dialog.
    
    Attributes:
        filter_node: The filter this item belongs to
    """
    _open_dialogs: list[QDialog] = []

    def __init__(self, filter_node: "FilterNode", parent: QGraphicsItem):
        super().__init__("resources/icons/settings.svg", parent)
        self.dialog = None
        self.filter_node = filter_node
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
            if self.dialog is None:
                self.dialog = FilterSettingsDialog(self.filter_node)
            self.dialog.show()


def check_if_filter_has_special_widget(filter_: Filter) -> NodeEditorFilterConfigWidget | None:
    """
    This method checks if there is a special configuration widget implemented for the given filter.
    In case there is, it will instantiate and return it. Otherwise, it will return None and leave the
    task of generating a generic one to the dialog.

    :param filter_: The filter to check for.
    :returns: The instantiates settings widget or None.
    """
    if 39 <= filter_.filter_type <= 43:
        return ColumnSelect(filter_)
    elif filter_.filter_type in [FilterTypeEnumeration.FILTER_TYPE_CUES, FilterTypeEnumeration.VFILTER_CUES]:
        return CueEditor(f=filter_)
    elif filter_.filter_type == 50:
        return LuaScriptConfigWidget()
    elif filter_.filter_type == int(FilterTypeEnumeration.VFILTER_AUTOTRACKER):
        return AutotrackerSettingsWidget()
    elif filter_.filter_type == int(FilterTypeEnumeration.VFILTER_EFFECTSSTACK):
        return EffectsStackFilterConfigWidget(filter_)
    else:
        return None


class FilterSettingsDialog(QDialog):
    """
    
    Attributes:
        filter: The filter whose settings this dialog displays
    """

    def __init__(self, filter_node: "FilterNode") -> None:
        super().__init__()
        self._filter_node = filter_node
        self.filter = filter_node.filter

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

        self._special_widget = check_if_filter_has_special_widget(self.filter)
        if self._special_widget:
            self._special_widget.configuration = self.filter.filter_configurations
            self._special_widget.parameters = self.filter.initial_parameters
            layout.addRow("", self._special_widget.get_widget())
        else:
            add_patch_info: bool = self.filter.filter_type == 11
            # Only add initial parameters section if present
            if len(self.filter.initial_parameters) > 0:
                layout.addRow("Initial Parameters", QLabel(""))
                for key, value in self.filter.initial_parameters.items():
                    line_edit = QLineEdit()
                    line_edit.setText(value)
                    line_edit.textChanged.connect(lambda new_value, _key=key: self._ip_value_changed(_key, new_value))
                    layout.addRow(key, line_edit)
            # Only add filter configuration section if present
            if len(self.filter.filter_configurations) > 0:
                layout.addRow("Filter Configurations", QLabel(""))
                for key, value in self.filter.filter_configurations.items():
                    line_edit = QLineEdit()
                    line_edit.setText(value)
                    line_edit.textChanged.connect(lambda new_value, _key=key: self._fc_value_changed(_key, new_value))
                    if add_patch_info:
                        key = self._add_patch_info(key, value)
                    layout.addRow(key, line_edit)
        self._ok_button = QPushButton("Ok")
        self._ok_button.pressed.connect(self.ok_button_pressed)

        layout.addRow("", self._ok_button)

        self.setLayout(layout)

    def _add_patch_info(self, key: str, value: str) -> str:
        if self.filter.filter_type != 11:
            return key
        # Only channel inputs have patching info
        if key == "universe":
            return key
        # Fetch universe
        universe_id = int(self.filter.filter_configurations["universe"])
        for uni in self.filter.scene.board_configuration.universes:
            if uni.universe_proto.id == universe_id:
                universe: Universe = uni
                break
        else:
            logger.warning("FilterSettingsItem: Could not find universe %s", universe_id)
            return key
        # Fetch patching short name
        for channel in universe.patching:
            try:
                if channel.address == int(value):
                    key = f"{key} : {channel.fixture.short_name}"
            except ValueError:
                # We've loaded from a generated filter. Nothing to do here
                pass
        return key

    def _ip_value_changed(self, key, value):
        self.filter.initial_parameters[key] = value

    def _fc_value_changed(self, key, value):
        self.filter.filter_configurations[key] = value

    def ok_button_pressed(self):
        if self._special_widget:
            self.filter.filter_configurations.update(self._special_widget.configuration)
            self.filter.initial_parameters.update(self._special_widget.parameters)
        self.close()

    def closeEvent(self, arg__1: PySide6.QtGui.QCloseEvent) -> None:
        if self._special_widget:
            self._special_widget.parent_closed(self._filter_node)
        else:
            self._filter_node.update_node_after_settings_changed()
        super().closeEvent(arg__1)

    def show(self) -> None:
        super().show()
        if self._special_widget:
            self._special_widget.parent_opened()
