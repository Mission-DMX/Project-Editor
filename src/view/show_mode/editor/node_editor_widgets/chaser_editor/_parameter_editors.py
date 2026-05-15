"""Contains widgets to modify settings of parameter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from model.filter_data.chaser_model import ChaserLayer, ChaserModel


class ColorParameter(QWidget):
    """Widget to configure a color parameter."""

    # TODO add widget with color label and color picker


class AbsoluteNumParameter(QWidget):
    """Widget to configure a absolute number parameter."""

    # TODO add widget with QSpinBox, maybe use inheritance


class PercentNumParameter(QWidget):
    """A widget to configure a relative number parameter."""

    def __init__(self, parameter_name: str, help_text: str, index_of_parameter_in_layer: int, layer: ChaserLayer,
                 parent_model: ChaserModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layer = layer
        self._index_of_parameter_in_layer = index_of_parameter_in_layer
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(parameter_name))
        self._use_channel_cb = QCheckBox("Use parameter")
        top_layout.addWidget(self._use_channel_cb)
        self._channel_combo_box = QComboBox()
        self._channel_combo_box.setEditable(False)
        self._channel_combo_box.setEnabled(False)
        self._channel_combo_box.addItems(parent_model.number_parameters)
        self._channel_combo_box.currentTextChanged.connect(self._channel_selected)
        top_layout.addWidget(self._channel_combo_box)
        self._control_widget = QSlider()
        self._control_widget.setRange(0, 65535)
        try:
            self._control_widget.setValue(int(layer.parameter_data[index_of_parameter_in_layer]))
        except ValueError:
            self._channel_combo_box.setCurrentText(layer.parameter_data[index_of_parameter_in_layer])
            self._use_channel_cb.setChecked(True)
        self._control_widget.valueChanged.connect(self._value_changed)
        layout.addLayout(top_layout)
        layout.addWidget(QLabel(help_text))
        self.setLayout(layout)

    def _use_param_cb_checked_changed(self) -> None:
        state = self._use_channel_cb.isChecked()
        self._channel_combo_box.setEnabled(state)
        self._control_widget.setEnabled(not state)

    def _channel_selected(self) -> None:
        if self._use_channel_cb.isChecked():
            self._layer.parameter_data[self._index_of_parameter_in_layer] = self._channel_combo_box.currentText()

    def _value_changed(self) -> None:
        if self._use_channel_cb.isChecked():
            return
        self._layer.parameter_data[self._index_of_parameter_in_layer] = str(self._control_widget.value())
