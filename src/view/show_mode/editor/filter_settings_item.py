"""Module for filter settings editor"""
import os.path
from logging import getLogger
from typing import TYPE_CHECKING

import PySide6
from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QDialog, QFormLayout, QGraphicsItem, QLabel, QLineEdit, QPushButton, QVBoxLayout

from model.filter import Filter, FilterTypeEnumeration
from utility import resource_path
from view.show_mode.editor.node_editor_widgets.cue_editor import CueEditor
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_widget import PanTiltConstantWidget
from view.show_mode.effect_stacks.filter_config_widget import EffectsStackFilterConfigWidget

from .node_editor_widgets import NodeEditorFilterConfigWidget
from .node_editor_widgets.autotracker_settings import AutotrackerSettingsWidget
from .node_editor_widgets.color_mixing_setup_widget import ColorMixingSetupWidget
from .node_editor_widgets.column_select import ColumnSelect
from .node_editor_widgets.import_vfilter_settings_widget import ImportVFilterSettingsWidget
from .node_editor_widgets.lua_widget import LuaScriptConfigWidget

if TYPE_CHECKING:
    from .nodes import FilterNode

logger = getLogger(__name__)


class FilterSettingsItem(QGraphicsSvgItem):
    """GraphicsItem to handle opening filter settings dialog.
    
    Attributes:
        filter_node: The filter this item belongs to
    """
    _open_dialogs: list[QDialog] = []

    def __init__(self, filter_node: "FilterNode", parent: QGraphicsItem, filter: Filter):
        super().__init__(resource_path(os.path.join("resources", "icons", "settings.svg")), parent)
        self.dialog = None
        self.filter_node = filter_node
        self.on_update = lambda: None
        self.setScale(0.2)
        self.moveBy(parent.boundingRect().width() / 2 - 6, parent.boundingRect().height() - 20)
        self._filter = filter
        self._mb_updated: bool = False

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
        if ev.key() == Qt.Key.Key_Enter or ev.key() == Qt.Key.Key_Return and self.on_update is not None:
            self.on_update()
            return
        super().keyPressEvent(ev)

    def mousePressEvent(self, ev):
        """Handle left mouse button click by opening filter settings dialog"""
        if not self._filter.configuration_supported:
            return
        if ev.button() == Qt.MouseButton.LeftButton:
            # TODO make sure that we're opening it in the same dialog, fixed to a screen unless settings request
            #  otherwise
            if self.dialog is not None:
                self.dialog.deleteLater()
            self.dialog = FilterSettingsDialog(self.filter_node)
            self.dialog.show()

    def paint(self, painter, option, widget=...):
        if not self._filter.configuration_supported:
            if not self._mb_updated:
                self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                self._mb_updated = True
        else:
            # TODO draw a round rect around borders
            super().paint(painter, option, widget)


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
    if filter_.filter_type in [FilterTypeEnumeration.FILTER_TYPE_CUES, FilterTypeEnumeration.VFILTER_CUES]:
        return CueEditor(f=filter_)
    if filter_.filter_type == 50:
        return LuaScriptConfigWidget()
    if filter_.filter_type == FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
        return PanTiltConstantWidget(filter_)
    if filter_.filter_type == int(FilterTypeEnumeration.VFILTER_AUTOTRACKER):
        return AutotrackerSettingsWidget()
    if filter_.filter_type == int(FilterTypeEnumeration.VFILTER_EFFECTSSTACK):
        return EffectsStackFilterConfigWidget(filter_)
    if filter_.filter_type == int(FilterTypeEnumeration.VFILTER_IMPORT):
        return ImportVFilterSettingsWidget(filter_)
    if filter_.filter_type == int(FilterTypeEnumeration.VFILTER_COLOR_MIXER):
        return ColorMixingSetupWidget(filter_)

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
        # Function pointer to handle patching information. Only set, when filter is universe filter

        self._special_widget = check_if_filter_has_special_widget(self.filter)
        if self._special_widget:
            layout = QVBoxLayout()
            self._special_widget.configuration = self.filter.filter_configurations
            self._special_widget.parameters = self.filter.initial_parameters
            layout.addWidget(self._special_widget.get_widget())
        else:
            layout = QFormLayout()
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

        if isinstance(layout, QFormLayout):
            layout.addRow("", self._ok_button)
        else:
            layout.addWidget(self._ok_button)

        self.setLayout(layout)

    def _add_patch_info(self, key: str, value: str) -> str:
        if self.filter.filter_type != 11:
            return key
        # Only channel inputs have patching info
        if key == "universe":
            return key
        universe_id = int(self.filter.filter_configurations["universe"])
        if not self.filter.scene.board_configuration.universe(universe_id):
            logger.warning("FilterSettingsItem: Could not find universe %s", universe_id)
            return key

        # Fetch patching short name
        key = "Empty"
        for fixture in self.filter.scene.board_configuration.fixtures:
            if fixture.universe_id == universe_id and value in range(fixture.start_index,
                                                                     fixture.start_index + fixture.channel_length + 1):
                key = f"{key} : {fixture.short_name}"
                break

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
