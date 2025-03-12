# coding=utf-8
"""This file contains a widget with a textfield and a button, extended by a list of buttons to update constants nodes
with a new value or predefined one in fish"""
import sys

from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from model import Filter, UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.show_mode.show_ui_widgets.constant_button_list import ConstantNumberButtonList


class ButtonsWithValueSubmit(UIWidget):
    """ UI widget for the showmode (extended with ConstantNumberButtonList also for the editor mode)
    Provides a textfield with a submit button to update a value (of a constant node),
    provides also (from ConstantNumberButtonList) a button list to send pre-defined values
    """
    def get_config_dialog_widget(self, parent) -> QWidget:
        return self._button_list.get_config_dialog_widget(parent)

    def __init__(self, fid: str, parent: "UIPage", filter_model: Filter, configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self._filter_type = filter_model.filter_type
        self._player_widget: QWidget | None = None
        self.associated_filters["constant"] = fid
        self._button_list = ConstantNumberButtonList(fid, self.parent, filter_model, configuration)

    def generate_update_content(self) -> list[tuple[str, str]]:
        return self._button_list.generate_update_content()

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget:
            self._player_widget.deleteLater()
        self.construct_player_widget(parent)
        return self._player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return self._button_list.get_configuration_widget(parent)

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        fid = self.associated_filters.get("constant")
        w = ButtonsWithValueSubmit(fid, self.parent,
                                   Filter(None, fid, self._filter_type, None, None),
                                   self.configuration.copy())
        super().copy_base(w)
        return w

    def construct_player_widget(self, parent: QWidget | None):
        widget = QWidget(parent)
        self._player_widget = QWidget(parent)
        self._player_widget.setMinimumWidth(50)
        self._player_widget.setMinimumHeight(30)
        layout = QHBoxLayout(widget)
        layoutSubmitOwnValue = QVBoxLayout(widget)
        valuefield = QDoubleSpinBox(widget)
        if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT:
            valuefield.setMaximum(sys.float_info.max)
            valuefield.setMinimum(-sys.float_info.max)
            valuefield.setDecimals(20)
        else:
            valuefield.setMaximum(self._button_list._maximum)
            valuefield.setDecimals(0)
        submitButton = QPushButton("Send Value", widget)
        def pressed_button():
            value = valuefield.value() if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT else int(valuefield.value())
            self._button_list._set_value(value)

        submitButton.clicked.connect(pressed_button)
        layoutSubmitOwnValue.addWidget(valuefield)
        layoutSubmitOwnValue.addWidget(submitButton)
        layout.addLayout(layoutSubmitOwnValue)
        buttons = self._button_list.get_player_widget(parent)
        layout.addWidget(buttons)
        self._player_widget.setLayout(layout)
