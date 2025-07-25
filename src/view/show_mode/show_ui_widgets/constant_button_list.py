from __future__ import annotations

import sys
from typing import override

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


class ConstantNumberButtonList(UIWidget):
    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
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
            self.configuration["buttons"] += \
                (f"{';' if len(self.configuration["buttons"]) else ''}"
                 f"{name_edit.text().replace(';', '').replace(':', '')}:"
                 f"{int(value_edit.value()) if self._maximum != -1 else value_edit.value()}")

            list_widget.addItem(f"{name_edit.text()} -> {value_edit.value()}")
            if self._configuration_widget:
                conf_button = QPushButton(name_edit.text(), self._configuration_widget)
                conf_button.setEnabled(False)
                conf_button.setMinimumWidth(max(30, len(name_edit.text()) * 10))
                conf_button.setMinimumHeight(30)
                wl = self._configuration_widget.layout()
                wl.addWidget(conf_button)
                self._configuration_widget.setLayout(wl)
                self._configuration_widget.parent().update_size()

        add_button.clicked.connect(add_action)
        return widget

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None
        self._model = None
        value_str = "0"
        if "." in value_str:
            self._value = float(value_str)
        else:
            self._value = int(value_str)
        self._filter_type = None
        self._value = 0

    def set_filter(self, f: Filter, i: int) -> None:
        if f is None:
            return
        super().set_filter(f, i)
        self._model = f
        self.associated_filters["constant"] = f.filter_id
        self._filter_type = f.filter_type
        self._value = float(
            f.initial_parameters["value"]) if f.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT else \
            int(f.initial_parameters["value"])
        self._maximum = 255 if f.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_8BIT \
            else -1 if f.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT else (2 ** 16) - 1

    def _set_value(self, new_value: float) -> None:
        self._value = new_value
        self.push_update()

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        return [("value", str(self._value))]

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget:
            self._player_widget.deleteLater()
        self.construct_player_widget(parent)
        return self._player_widget

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if not self._configuration_widget:
            self.construct_configuration_widget(parent)
        return self._configuration_widget

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = ConstantNumberButtonList(self.parent, self.configuration.copy())
        w.set_filter(self._model, 0)
        super().copy_base(w)
        return w

    def construct_player_widget(self, parent: QWidget | None) -> None:
        self._player_widget = QWidget(parent)
        self._player_widget.setMinimumWidth(50)
        self._player_widget.setMinimumHeight(30)
        layout = QHBoxLayout()
        if "buttons" in self.configuration:
            for value_name_tuple in self.configuration["buttons"].split(";"):
                name, value = value_name_tuple.split(":")
                value = float(value) if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT else int(value)
                button = QPushButton(name, self._player_widget)
                button.clicked.connect(lambda _value=value: self._set_value(_value))
                button.setMinimumWidth(max(30, len(name) * 10))
                button.setMinimumHeight(30)
                layout.addWidget(button)
        self._player_widget.setLayout(layout)

    def construct_configuration_widget(self, parent: QWidget | None) -> None:
        self._configuration_widget = QWidget(parent)
        self._configuration_widget.setMinimumWidth(50)
        self._configuration_widget.setMinimumHeight(30)
        layout = QHBoxLayout()
        button_configuration = self.configuration.get("buttons")
        if button_configuration:
            for value_name_tuple in button_configuration.split(";"):
                name, _ = value_name_tuple.split(":")
                button = QPushButton(name, self._player_widget)
                button.setEnabled(False)
                button.setMinimumWidth(max(30, len(name) * 10))
                button.setMinimumHeight(30)
                layout.addWidget(button)
        self._configuration_widget.setLayout(layout)

    def __str__(self) -> str:
        return str(self._model.filter_id if self._model else "Error: No Filter configured.")
