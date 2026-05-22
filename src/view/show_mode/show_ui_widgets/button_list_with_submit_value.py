"""File contains ButtonsWithValueSubmit module."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from model.filter import FilterTypeEnumeration
from view.show_mode.show_ui_widgets.constant_button_list import ConstantNumberButtonList

if TYPE_CHECKING:
    import proto.FilterMode_pb2
    from model import UIPage

class ButtonsWithValueSubmit(ConstantNumberButtonList):
    """UI widget for the show mode (extended with ConstantNumberButtonList also for the editor mode).

    Provides a textfield with a submit-button to update a value (of a constant node).
    Provides also (from ConstantNumberButtonList) a button list to send pre-defined values.

    """

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize UI widget."""
        super().__init__(parent, configuration)
        self._filter_type = None
        self._player_widget: QWidget | None = None
        self._spinbox: QDoubleSpinBox | None = None

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        w = super().get_player_widget(parent)
        return self._append_direct_widget(w, player=True)

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        w = super().get_configuration_widget(parent)
        return self._append_direct_widget(w)

    def _append_direct_widget(self, existing_widget: QWidget, player: bool = False) -> QWidget:
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        layout_submit_own_value = QVBoxLayout()
        valuefield = QDoubleSpinBox(top_widget)
        if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT:
            valuefield.setMaximum(sys.float_info.max)
            valuefield.setMinimum(-sys.float_info.max)
            valuefield.setDecimals(20)
        else:
            valuefield.setMaximum(self._maximum)
            valuefield.setMinimum(0)
            valuefield.setDecimals(0)
        if player:
            self._spinbox = valuefield
        submit_button = QPushButton("Send Value", top_widget)

        def pressed_button() -> None:
            value = valuefield.value() if self._filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT else int(
                valuefield.value())
            self._set_value(value)

        submit_button.clicked.connect(pressed_button)
        layout_submit_own_value.addWidget(valuefield)
        layout_submit_own_value.addWidget(submit_button)
        top_layout.addLayout(layout_submit_own_value)

        top_layout.addWidget(existing_widget)
        top_widget.setLayout(top_layout)
        return top_widget

    @override
    def _update_from_fish(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        super()._update_from_fish(param)
        if self._spinbox is not None and param.parameter_key == "value":
            self._spinbox.setValue(float(param.parameter_value))
