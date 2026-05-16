"""Contains widgets to modify settings of parameter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from model.color_hsi import ColorHSI
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorLabel

if TYPE_CHECKING:
    from model.filter_data.chaser_model import ChaserLayer, ChaserModel


class ColorParameter(QWidget):
    """Widget to configure a color parameter."""

    def __init__(self, parameter_name: str, help_text: str, index_of_parameter_in_layer: int, layer: ChaserLayer,
                 parent_model: ChaserModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layer_index = index_of_parameter_in_layer
        self._layer = layer

        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(parameter_name))
        self._use_channel_cb = QCheckBox("Use parameter")
        self._use_channel_cb.checkStateChanged.connect(self._use_param_cb_checked_changed)
        top_layout.addWidget(self._use_channel_cb)
        self._channel_combo_box = QComboBox()
        self._channel_combo_box.setEditable(False)
        self._channel_combo_box.setEnabled(False)
        self._channel_combo_box.addItems(parent_model.color_parameters)
        self._channel_combo_box.currentTextChanged.connect(self._channel_selected)
        top_layout.addWidget(self._channel_combo_box)
        self._color_label = ColorLabel()
        top_layout.addWidget(self._color_label)
        self._color_dialog: QColorDialog | None = None
        self._select_color_button = QPushButton("Select color")
        self._select_color_button.clicked.connect(self._change_color_clicked)
        top_layout.addWidget(self._select_color_button)
        param_data = layer.parameter_data[index_of_parameter_in_layer]
        self._use_channel_cb.setChecked(param_data in parent_model.color_parameters)
        if isinstance(param_data, ColorHSI):
            self._color_label.set_color(param_data)
        else:
            self._channel_combo_box.setCurrentText(param_data)
        layout.addLayout(top_layout)
        layout.addWidget(QLabel(help_text))
        self.setLayout(layout)

    def _use_param_cb_checked_changed(self) -> None:
        state = self._use_channel_cb.isChecked()
        self._channel_combo_box.setEnabled(state)
        self._select_color_button.setEnabled(not state)
        if state:
            self._layer.parameter_data[self._layer_index] = self._channel_combo_box.currentText()
        else:
            self._layer.parameter_data[self._layer_index] = self._color_label.get_color()

    def _channel_selected(self) -> None:
        if self._use_channel_cb.isChecked():
            self._layer.parameter_data[self._layer_index] = self._channel_combo_box.currentText()

    def _change_color_clicked(self) -> None:
        self._color_dialog = QColorDialog()
        parameter_data = self._layer.parameter_data[self._layer_index]
        if isinstance(parameter_data, ColorHSI):
            self._color_dialog.setCurrentColor(parameter_data.to_qt_color())
        self._color_dialog.setModal(True)
        self._color_dialog.accepted.connect(self._color_selected)
        self._color_dialog.show()

    def _color_selected(self) -> None:
        new_color = ColorHSI.from_qt_color(self._color_dialog.currentColor())
        self._layer.parameter_data[self._layer_index] = new_color
        self._color_label.set_color(new_color)
        self._color_dialog.deleteLater()
        self._color_dialog = None


class NumberParameter(QWidget):
    """Base class for both number parameters."""

    def __init__(self, parameter_name: str, help_text: str, index_of_parameter_in_layer: int, layer: ChaserLayer,
                 parent_model: ChaserModel, widget_class: QSlider | QSpinBox, parent: QWidget | None = None) -> None:
        """Initialize the widget using the given widget class."""
        super().__init__(parent)
        self._layer = layer
        self._index_of_parameter_in_layer = index_of_parameter_in_layer
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(parameter_name))
        self._use_channel_cb = QCheckBox("Use parameter")
        self._use_channel_cb.checkStateChanged.connect(self._use_param_cb_checked_changed)
        top_layout.addWidget(self._use_channel_cb)
        self._channel_combo_box = QComboBox()
        self._channel_combo_box.setEditable(False)
        self._channel_combo_box.setEnabled(False)
        self._channel_combo_box.addItems(parent_model.number_parameters)
        self._channel_combo_box.currentTextChanged.connect(self._channel_selected)
        top_layout.addWidget(self._channel_combo_box)
        self._control_widget: QSlider | QSpinBox = widget_class
        self._control_widget.setRange(0, 65535)

        param_data = layer.parameter_data[index_of_parameter_in_layer]
        if isinstance(param_data, int):
            self._control_widget.setValue(param_data)
        else:
            self._channel_combo_box.setCurrentText(param_data)
            self._use_channel_cb.setChecked(True)
        self._control_widget.valueChanged.connect(self._value_changed)
        top_layout.addWidget(self._control_widget)
        layout.addLayout(top_layout)
        layout.addWidget(QLabel(help_text))
        self.setLayout(layout)

    def _use_param_cb_checked_changed(self) -> None:
        state = self._use_channel_cb.isChecked()
        self._channel_combo_box.setEnabled(state)
        self._control_widget.setEnabled(not state)
        if state:
            self._layer.parameter_data[self._index_of_parameter_in_layer] = self._channel_combo_box.currentText()
        else:
            self._layer.parameter_data[self._index_of_parameter_in_layer] = self._control_widget.value()

    def _channel_selected(self) -> None:
        if self._use_channel_cb.isChecked():
            self._layer.parameter_data[self._index_of_parameter_in_layer] = self._channel_combo_box.currentText()

    def _value_changed(self) -> None:
        if self._use_channel_cb.isChecked():
            return
        self._layer.parameter_data[self._index_of_parameter_in_layer] = self._control_widget.value()


class AbsoluteNumParameter(NumberParameter):
    """Widget to configure a absolute number parameter."""

    def __init__(self, parameter_name: str, help_text: str, index_of_parameter_in_layer: int, layer: ChaserLayer,
                 parent_model: ChaserModel, parent: QWidget | None = None) -> None:
        """Initialize the widget."""
        super().__init__(
            parameter_name,
            help_text,
            index_of_parameter_in_layer,
            layer,
            parent_model,
            QSpinBox(),
            parent
        )


class PercentNumParameter(NumberParameter):
    """A widget to configure a relative number parameter."""

    def __init__(self, parameter_name: str, help_text: str, index_of_parameter_in_layer: int, layer: ChaserLayer,
                 parent_model: ChaserModel, parent: QWidget | None = None) -> None:
        """Initialize the widget."""
        super().__init__(
            parameter_name,
            help_text,
            index_of_parameter_in_layer,
            layer,
            parent_model,
            QSlider(),
            parent
        )
