"""This file contains a widget with a textfield and a button, extended by a list of buttons to update constants nodes
with a new value or predefined one in fish"""
import sys
from typing import override

from PySide6.QtWidgets import QDialog, QDoubleSpinBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from model import Filter, UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.show_mode.show_ui_widgets.constant_button_list import ConstantNumberButtonList


class ButtonsWithValueSubmit(UIWidget):
    """ UI widget for the showmode (extended with ConstantNumberButtonList also for the editor mode)
    Provides a textfield with a submit button to update a value (of a constant node),
    provides also (from ConstantNumberButtonList) a button list to send pre-defined values
    """

    @override
    def get_config_dialog_widget(self, parent:QDialog) -> QWidget:
        return self._button_list.get_config_dialog_widget(parent)

    def __init__(self, parent: "UIPage", configuration: dict[str, str]) -> None:
        super().__init__(parent, configuration)
        self._filter_type = None
        self._player_widget: QWidget | None = None
        self._button_list = ConstantNumberButtonList(self.parent, configuration)

    def set_filter(self, f: Filter, i: int) -> None:
        super().set_filter(f, i)
        self._filter_type = f.filter_type
        self._button_list.set_filter(f, i)
        self.associated_filters["constant"] = f.filter_id

    def generate_update_content(self) -> list[tuple[str, str]]:
        return self._button_list.generate_update_content()

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget:
            self._player_widget.deleteLater()
        self.construct_player_widget(parent)
        return self._player_widget

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return self._button_list.get_configuration_widget(parent)

    @override
    def copy(self, new_parent: "UIPage") -> "UIWidget":
        fid = self.associated_filters.get("constant")
        w = ButtonsWithValueSubmit(self.parent, self.configuration.copy())
        w.set_filter(Filter(None, fid, self._filter_type, None, None), 0)
        super().copy_base(w)
        return w

    def construct_player_widget(self, parent: QWidget | None) -> None:
        widget = QWidget(parent)
        self._player_widget = QWidget(parent)
        self._player_widget.setMinimumWidth(50)
        self._player_widget.setMinimumHeight(30)
        layout = QHBoxLayout(widget)
        layout_submit_own_value = QVBoxLayout(widget)
        valuefield = QDoubleSpinBox(widget)
        if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT:
            valuefield.setMaximum(sys.float_info.max)
            valuefield.setMinimum(-sys.float_info.max)
            valuefield.setDecimals(20)
        else:
            valuefield.setMaximum(self._button_list._maximum)
            valuefield.setDecimals(0)
        submit_button = QPushButton("Send Value", widget)

        def pressed_button() -> None:
            value = valuefield.value() if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT else int(
                valuefield.value())
            self._button_list._set_value(value)

        submit_button.clicked.connect(pressed_button)
        layout_submit_own_value.addWidget(valuefield)
        layout_submit_own_value.addWidget(submit_button)
        layout.addLayout(layout_submit_own_value)
        buttons = self._button_list.get_player_widget(parent)
        layout.addWidget(buttons)
        self._player_widget.setLayout(layout)

    def __str__(self) -> str:
        return str(self.configuration.get("constant"))
