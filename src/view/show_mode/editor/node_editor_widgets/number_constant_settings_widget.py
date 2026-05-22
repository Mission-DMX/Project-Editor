"""Contains editor widget for number constants."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QFormLayout, QSpinBox, QWidget

from model import DataType
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget

if TYPE_CHECKING:
    from model import Filter


class NumberConstantSettingsWidget(NodeEditorFilterConfigWidget):
    """Widget to set the requested number and provide feedback check box.

    Toggling the feedback check box changes the filter type of the connected filter.

    """

    def __init__(self, _filter: Filter) -> None:
        """Initialize widget using given parent."""
        super().__init__()
        self._filter = _filter
        if isinstance(_filter.filter_type, int):
            _filter.filter_type = FilterTypeEnumeration(_filter.filter_type)
        if _filter.filter_type in [
            FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT]:
            self._data_type = DataType.DT_8_BIT
        elif _filter.filter_type in [
            FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT]:
            self._data_type = DataType.DT_16_BIT
        else:
            self._data_type = DataType.DT_DOUBLE
        self._widget = QWidget()
        layout = QFormLayout()
        match self._data_type:
            case DataType.DT_8_BIT:
                self._value_widget = QSpinBox(self._widget)
                self._value_widget.setMinimum(0)
                self._value_widget.setMaximum(255)
            case DataType.DT_16_BIT:
                self._value_widget = QSpinBox(self._widget)
                self._value_widget.setMinimum(0)
                self._value_widget.setMaximum(65535)
            case _:
                self._value_widget = QDoubleSpinBox(self._widget)
        layout.addRow("Value", self._value_widget)
        self._response_cb = QCheckBox("Send Feedback to GUI", self._widget)
        self._response_cb.setChecked(_filter.filter_type in [
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT,
            FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_FLOAT
        ])
        layout.addWidget(self._response_cb)
        self._widget.setLayout(layout)

    @override
    def _get_parameters(self) -> dict[str, str]:
        if self._response_cb.isChecked():
            if self._data_type == DataType.DT_8_BIT:
                self._filter.filter_type = FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT
            elif self._data_type == DataType.DT_16_BIT:
                self._filter.filter_type = FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT
            else:
                self._filter.filter_type = FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_FLOAT
        else:
            if self._data_type == DataType.DT_8_BIT:
                self._filter.filter_type = FilterTypeEnumeration.FILTER_CONSTANT_8BIT
            elif self._data_type == DataType.DT_16_BIT:
                self._filter.filter_type = FilterTypeEnumeration.FILTER_CONSTANT_16_BIT
            else:
                self._filter.filter_type = FilterTypeEnumeration.FILTER_CONSTANT_FLOAT
        return {
            "value": str(self._value_widget.value()),
        }

    @override
    def _load_parameters(self, conf: dict[str, str]) -> None:
        if self._data_type == DataType.DT_DOUBLE:
            self._value_widget.setValue(float(conf.get("value", "0")))
        else:
            self._value_widget.setValue(int(conf.get("value", "0")))

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_configuration(self, parameters: dict[str, str]) -> dict:
        pass  # Nothing to do here

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {}

    @override
    def parent_opened(self) -> None:
        pass  # Nothing to do here
