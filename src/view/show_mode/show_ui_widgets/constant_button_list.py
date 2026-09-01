"""Show UI widgets to update constant filter values."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import (
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

from model import Filter, UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor._widget_holder import UIWidgetHolder

if TYPE_CHECKING:
    import proto.FilterMode_pb2
    from model import Scene


class ConstantNumberButtonList(UIWidget):
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
            value_edit.setMinimum(sys.float_info.max)
            value_edit.setDecimals(20)
        else:
            value_edit.setMaximum(self._maximum)
            value_edit.setDecimals(0)
        row_layout2.addWidget(value_edit)
        layout.addLayout(row_layout2)
        add_button = QPushButton("Add Button", widget)
        layout.addWidget(add_button)
        list_widget = QListWidget(widget)
        bc = self.configuration.get("buttons")
        if bc:
            for entry in bc.split(";"):
                name, value = entry.split(":")
                list_widget.addItem(f"{name} -> {value}")
        layout.addWidget(list_widget)
        widget.setLayout(layout)

        def add_action() -> None:
            if not self.configuration.get("buttons"):
                self.configuration["buttons"] = ""
            self.configuration["buttons"] += (
                f"{';' if len(self.configuration['buttons']) else ''}"
                f"{name_edit.text().replace(';', '').replace(':', '')}:"
                f"{int(value_edit.value()) if self._maximum != -1 else value_edit.value()}"
            )

            list_widget.addItem(f"{name_edit.text()} -> {value_edit.value()}")
            if self._configuration_widget:
                conf_button = QPushButton(name_edit.text(), self._configuration_widget)
                conf_button.setEnabled(False)
                conf_button.setMinimumWidth(max(30, len(name_edit.text()) * 10))
                conf_button.setMinimumHeight(30)
                wl = self._configuration_widget.layout()
                wl.addWidget(conf_button)
                self._configuration_widget.setLayout(wl)
                holder = self._configuration_widget.parent()
                while not isinstance(holder, UIWidgetHolder) and holder is not None:
                    holder = holder.parent()
                if holder is not None:
                    holder.update_size()

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
        self._model = None
        self._filter_type = None
        self._value = 0
        self._maximum = -1
        self._registered_callback_key: tuple[Scene, str] | None = None
        self._player_buttons: dict[float, QPushButton] = {}

    def __del__(self) -> None:
        """Unregister the fish update callback (fallback in case close was not called)."""
        self._unregister_fish_callback()

    @override
    def close(self) -> None:
        """Unregister the fish update callback as this widget is being removed."""
        self._unregister_fish_callback()

    def _unregister_fish_callback(self) -> None:
        """Remove the update callback registered for the linked filter, if any."""
        if self._registered_callback_key is None:
            return
        scene, filter_id = self._registered_callback_key
        self._registered_callback_key = None
        scene.board_configuration.remove_filter_update_callback(scene, filter_id, self._update_from_fish)

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
        if f is None:
            return
        super().set_filter(f, i)
        self._model = f
        self.associated_filters["constant"] = f.filter_id
        self._filter_type = f.filter_type
        value_str = f.initial_parameters.get("value", "0")
        self._value = float(value_str) if self._is_float_filter else int(float(value_str))
        match f.filter_type:
            case FilterTypeEnumeration.FILTER_CONSTANT_8BIT | FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT:
                self._maximum = 255
            case FilterTypeEnumeration.FILTER_CONSTANT_16_BIT | FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT:
                self._maximum = (2**16) - 1
            case _:
                self._maximum = -1
        if self._registered_callback_key != (f.scene, f.filter_id):
            self._unregister_fish_callback()
            f.scene.board_configuration.register_filter_update_callback(f.scene, f.filter_id, self._update_from_fish)
            self._registered_callback_key = (f.scene, f.filter_id)

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
        layout.addWidget(self._player_widget)
        w.setLayout(layout)
        return w

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        w = QWidget(parent)
        self._construct_configuration_widget(w)
        layout = QHBoxLayout()
        layout.addWidget(self._configuration_widget)
        w.setLayout(layout)
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = type(self)(new_parent, self.configuration.copy())
        w.set_filter(self._model, 0)
        super().copy_base(w)
        return w

    def _construct_player_widget(self, parent: QWidget | None) -> None:
        """Construct a usable widget."""
        self._player_widget = QWidget(parent)
        self._player_widget.setMinimumHeight(30)
        layout = QHBoxLayout()
        total_min_width = 0
        self._player_buttons.clear()
        button_configuration = self.configuration.get("buttons")
        if button_configuration:
            for value_name_tuple in button_configuration.split(";"):
                name, value = value_name_tuple.split(":")
                value = float(value) if self._is_float_filter else int(float(value))
                button = QPushButton(name, self._player_widget)
                button.clicked.connect(lambda _, _value=value: self._set_value(_value))
                button.setMinimumWidth(max(30, len(name) * 15))
                total_min_width += button.minimumSizeHint().width()
                button.setMinimumHeight(30)
                layout.addWidget(button)
                self._player_buttons[value] = button
        self._player_widget.setLayout(layout)
        self._player_widget.setMinimumWidth(max(50, 2 * total_min_width))

    def _construct_configuration_widget(self, parent: QWidget | None) -> None:
        """Construct placeholder widget."""
        self._configuration_widget = QWidget(parent)
        self._configuration_widget.setMinimumHeight(30)
        layout = QHBoxLayout()
        button_configuration = self.configuration.get("buttons")
        total_min_width = 0
        if button_configuration:
            for value_name_tuple in button_configuration.split(";"):
                name, _ = value_name_tuple.split(":")
                button = QPushButton(name, self._configuration_widget)
                button.setEnabled(False)
                min_width = max(30, len(name) * 15)
                button.setMinimumWidth(min_width)
                total_min_width += button.minimumSizeHint().width()
                button.setMinimumHeight(30)
                layout.addWidget(button)
        self._configuration_widget.setLayout(layout)
        self._configuration_widget.setMinimumWidth(max(50, total_min_width))

    def __str__(self) -> str:
        """Get the filter id string or an error message."""
        return str(self._model.filter_id if self._model else "Error: No Filter configured.")

    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        if param.parameter_key != "value":
            return
        try:
            new_value = float(param.parameter_value)
        except ValueError:
            return
        try:
            for button in self._player_buttons.values():
                button.setDown(False)
            next_button = self._player_buttons.get(new_value)
            if next_button is not None:
                next_button.setDown(True)
        except RuntimeError:
            self._player_buttons.clear()
