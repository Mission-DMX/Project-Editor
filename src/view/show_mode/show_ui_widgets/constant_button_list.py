"""Show UI widgets to update constant filter values."""

from __future__ import annotations

import sys
from math import isnan, nan
from typing import TYPE_CHECKING, cast, override

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from model import Filter, FilterUpdateCallbackMixin, UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor._widget_holder import UIWidgetHolder
from view.show_mode.show_ui_widgets.slider_constant_ctrl_uiwidget import _parse_config_float, _parse_config_int

if TYPE_CHECKING:
    import proto.FilterMode_pb2


def _parse_button_entries(raw: str | None) -> list[tuple[str, str]]:
    """Parse a button list configuration into name and raw value pairs.

    Args:
        raw: The raw ``buttons`` configuration string (``name:value;name:value``), or None.

    Returns:
        The parsed pairs in configuration order. Malformed entries - empty segments from stray
        separators, missing separators, empty names or non-numeric values - are skipped.

    """
    entries: list[tuple[str, str]] = []
    if not raw:
        return entries
    for entry in raw.split(";"):
        name, separator, raw_value = entry.partition(":")
        if not separator or not name or not raw_value:
            continue
        if isnan(_parse_config_float(raw_value, nan)):
            continue
        entries.append((name, raw_value))
    return entries


class ConstantNumberButtonList(FilterUpdateCallbackMixin, UIWidget):
    """Show UI widget to provide the user with configurable buttons that alter the content of a constant filter."""

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        """Provide a configuration widget for button control."""
        # TODO add option to configure images instead of text (to be used as GOBO select or color wheel choice etc.)
        widget = QWidget(parent)
        layout = QVBoxLayout()
        row_layout1 = QHBoxLayout()
        row_layout1.addWidget(QLabel("Button Text:", widget))
        name_edit = QLineEdit(widget)
        row_layout1.addWidget(name_edit)
        layout.addLayout(row_layout1)
        row_layout2 = QHBoxLayout()
        row_layout2.addWidget(QLabel("Value to set:", widget))
        value_edit = QDoubleSpinBox(widget)
        if self._maximum == -1:
            value_edit.setMaximum(sys.float_info.max)
            value_edit.setMinimum(-sys.float_info.max)
            value_edit.setDecimals(20)
        else:
            value_edit.setMaximum(self._maximum)
            value_edit.setDecimals(0)
        row_layout2.addWidget(value_edit)
        layout.addLayout(row_layout2)
        add_button = QPushButton("Add Button", widget)
        layout.addWidget(add_button)
        flash_checkbox = QCheckBox("Flash button behavior", widget)
        flash_checkbox.setChecked(self.configuration.get("flash_behaviour", "false") == "true")

        def flash_toggled(checked: bool) -> None:
            self.configuration["flash_behaviour"] = "true" if checked else "false"

        flash_checkbox.toggled.connect(flash_toggled)
        layout.addWidget(flash_checkbox)
        list_widget = QListWidget(widget)
        for name, value in _parse_button_entries(self.configuration.get("buttons")):
            list_widget.addItem(f"{name} -> {value}")
        layout.addWidget(list_widget)
        widget.setLayout(layout)

        def add_action() -> None:
            button_name = name_edit.text().strip().replace(";", "").replace(":", "")
            if not button_name:
                return
            if not self.configuration.get("buttons"):
                self.configuration["buttons"] = ""
            self.configuration["buttons"] += (
                f"{';' if len(self.configuration['buttons']) else ''}"
                f"{button_name}:"
                f"{int(value_edit.value()) if self._maximum != -1 else value_edit.value()}"
            )

            list_widget.addItem(f"{button_name} -> {value_edit.value()}")
            if self._configuration_widget:
                conf_button = QPushButton(button_name, self._configuration_widget)
                conf_button.setEnabled(False)
                conf_button.setMinimumWidth(max(30, len(button_name) * 10))
                conf_button.setMinimumHeight(30)
                wl = self._configuration_widget.layout()
                if wl is not None:
                    wl.addWidget(conf_button)
                    self._configuration_widget.setLayout(wl)
            self._rebuild_player_widget()
            self._notify_size_change()

        add_button.clicked.connect(add_action)
        return widget

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Button list UI widget.

        Args:
            parent: The parent widget page.
            configuration: The configuration of this widget.

        """
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None
        self._model: Filter | None = None
        self._filter_type: FilterTypeEnumeration | None = None
        self._value: int | float = 0
        self._default_value: int | float = 0
        self._maximum = -1
        self._player_buttons: dict[float, list[QPushButton]] = {}

    @property
    def _is_float_filter(self) -> bool:
        """Return whether the linked filter is a (responding) float constant filter."""
        return self._filter_type in (
            FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_FLOAT,
        )

    def set_filter(self, f: Filter, i: int) -> None:
        """Set the filter associated with this UI widget for a specific button.

        Args:
            f: The new filter to set
            i: The index of the button to update.

        """
        if not f:
            return
        super().set_filter(f, i)
        self._model = f
        self.associated_filters["constant"] = f.filter_id
        self._filter_type = cast("FilterTypeEnumeration", f.filter_type)
        raw_value = f.initial_parameters.get("value", "0")
        self._default_value = (
            _parse_config_float(raw_value, 0.0) if self._is_float_filter else _parse_config_int(raw_value, 0)
        )
        self._value = self._default_value
        match f.filter_type:
            case FilterTypeEnumeration.FILTER_CONSTANT_8BIT | FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT:
                self._maximum = 255
            case FilterTypeEnumeration.FILTER_CONSTANT_16_BIT | FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT:
                self._maximum = (2**16) - 1
            case _:
                self._maximum = -1
        self._register_fish_callback(f)

    @override
    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """Move the linked constant filter id and the fish callback along when the filter is renamed."""
        super().notify_id_rename(old_id, new_id)
        self._handle_filter_id_rename(old_id, new_id)

    def _set_value(self, new_value: float) -> None:
        self._value = new_value
        self.push_update()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        return [("value", str(self._value))]

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        w = QWidget(parent)
        self._construct_player_widget(w)
        layout = QHBoxLayout()
        if self._player_widget is not None:
            layout.addWidget(self._player_widget)
        w.setLayout(layout)
        return w

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        w = QWidget(parent)
        self._construct_configuration_widget(w)
        layout = QHBoxLayout()
        if self._configuration_widget is not None:
            layout.addWidget(self._configuration_widget)
        w.setLayout(layout)
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        """Create a deep copy of this widget, re-linking the copied filter within the new parent's scene."""
        w = type(self)(new_parent, self.configuration.copy())
        super().copy_base(w)
        linked_filter_id = self.associated_filters.get("constant")
        if linked_filter_id is not None:
            linked_filter = new_parent.scene.get_filter_by_id(linked_filter_id)
            if linked_filter is not None:
                w.set_filter(linked_filter, 0)
        return w

    def _construct_player_widget(self, parent: QWidget | None) -> None:
        """Construct a usable widget."""
        self._player_widget = QWidget(parent)
        self._player_widget.setMinimumHeight(30)
        layout = QHBoxLayout()
        flash_behaviour = self.configuration.get("flash_behaviour", "false") == "true"
        total_min_width = 0
        self._player_buttons.clear()
        for name, raw_value in _parse_button_entries(self.configuration.get("buttons")):
            button_value = (
                _parse_config_float(raw_value, 0.0) if self._is_float_filter else _parse_config_int(raw_value, 0)
            )
            button = QPushButton(name, self._player_widget)
            if flash_behaviour:
                button.pressed.connect(lambda _value=button_value: self._set_value(_value))
                button.released.connect(lambda: self._set_value(self._default_value))
            else:
                button.clicked.connect(lambda _value=button_value: self._set_value(_value))
            button.setMinimumWidth(max(30, len(name) * 10))
            total_min_width += button.minimumSizeHint().width()
            button.setMinimumHeight(30)
            layout.addWidget(button)
            self._player_buttons.setdefault(button_value, []).append(button)
        self._player_widget.setLayout(layout)
        self._player_widget.setMinimumWidth(max(50, 2 * total_min_width))

    def _construct_configuration_widget(self, parent: QWidget | None) -> None:
        """Construct placeholder widget."""
        self._configuration_widget = QWidget(parent)
        self._configuration_widget.setMinimumHeight(30)
        layout = QHBoxLayout()
        total_min_width = 0
        for name, _ in _parse_button_entries(self.configuration.get("buttons")):
            button = QPushButton(name, self._configuration_widget)
            button.setEnabled(False)
            min_width = max(30, len(name) * 10)
            button.setMinimumWidth(min_width)
            total_min_width += button.minimumSizeHint().width()
            button.setMinimumHeight(30)
            layout.addWidget(button)
        self._configuration_widget.setLayout(layout)
        self._configuration_widget.setMinimumWidth(max(50, total_min_width))

    def _rebuild_player_widget(self) -> None:
        """Rebuild the player widget in place so that configuration changes become visible immediately.

        The old player widget is replaced within its parent layout and destroyed, and the tracked
        player buttons are rebuilt from the current configuration. Nothing happens if no player
        widget was constructed yet or if its Qt object was already destroyed.
        """
        old_widget = self._player_widget
        if old_widget is None:
            return
        try:
            parent = old_widget.parentWidget()
            if parent is None:
                return
            layout = parent.layout()
            if layout is None:
                return
            self._construct_player_widget(parent)
            new_widget = self._player_widget
            if new_widget is None:  # defensive: _construct_player_widget always sets a widget
                return
            layout.replaceWidget(old_widget, new_widget)
            old_widget.deleteLater()
        except RuntimeError:
            return

    def _notify_size_change(self) -> None:
        """Inform the enclosing widget holders about changed widget dimensions."""
        for widget in (self._player_widget, self._configuration_widget):
            if widget is None:
                continue
            try:
                ancestor: QWidget | None = widget.parentWidget()
                while ancestor is not None:
                    if isinstance(ancestor, UIWidgetHolder):
                        ancestor.update_size()
                        break
                    ancestor = ancestor.parentWidget()
            except RuntimeError:
                continue

    def __str__(self) -> str:
        """Get the filter id string or an error message."""
        return str(self._model.filter_id if self._model else "Error: No Filter configured.")

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Update the currently pressed buttons from a fish update.

        All buttons sharing the value of the update are highlighted together; unparseable or
        non-finite update values are ignored so that the last button state is kept.
        """
        if param.parameter_key != "value":
            return
        new_value = _parse_config_float(param.parameter_value, nan)
        if isnan(new_value):
            return
        try:
            for buttons in self._player_buttons.values():
                for button in buttons:
                    button.setDown(False)
            next_buttons = self._player_buttons.get(new_value)
            if next_buttons is not None:
                for button in next_buttons:
                    button.setDown(True)
        except RuntimeError:
            self._player_buttons.clear()
