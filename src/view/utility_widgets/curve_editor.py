# coding=utf-8
"""This file contains a widget that allows the editing and visualization of parameters of a trigonometric curve."""

import numpy
from math import pi
from PySide6.QtGui import QPalette

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QDoubleSpinBox, QLabel, QRadioButton, QFormLayout, \
    QCheckBox

from typing import TYPE_CHECKING

from pyqtgraph import PlotWidget, mkPen

from model.curve_configuration import CurveConfiguration, BaseCurve

from logging import getLogger
logger = getLogger(__file__)

if TYPE_CHECKING:
    pass


class _WaveRenderer(PlotWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._curve_configuration: CurveConfiguration = CurveConfiguration()
        self.setYRange(2, -2)
        self.setXRange(0, 360)
        self._data_line = self.plot()
        self._data_line.setPen(mkPen(width=3, color="#CC00AA"))
        self.setBackground(QPalette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window))

    def replot(self):
        steps = 3600
        x = numpy.linspace(0.0, 360.0, steps, dtype=numpy.float32)
        if self._curve_configuration.append_features_using_addition:
            y = numpy.zeros(steps, dtype=numpy.float32)
            concat_method = numpy.add
        else:
            y = numpy.ones(steps, dtype=numpy.float32)
            concat_method = numpy.multiply
        base_phase = self._curve_configuration.base_phase
        base_amplitude = self._curve_configuration.base_amplitude
        features = self._curve_configuration.selected_features
        if features & BaseCurve.SIN:
            y = concat_method(y, numpy.multiply(
                numpy.sin(numpy.multiply(numpy.add(x, base_phase), 2*pi/360.0*self._curve_configuration.frequencies[BaseCurve.SIN])),
                base_amplitude
            ))
            # TODO implement sin config
        if features & BaseCurve.COS:
            y = concat_method(y, numpy.multiply(
                numpy.cos(numpy.multiply(numpy.add(x, base_phase), 2*pi/360.0*self._curve_configuration.frequencies[BaseCurve.COS])),
                base_amplitude
            ))
            # TODO implement cos config
        if features & BaseCurve.TAN:
            # TODO tan config
            y = concat_method(y, numpy.multiply(
                numpy.tan(numpy.multiply(numpy.add(x, base_phase), 2*pi/360.0*self._curve_configuration.frequencies[BaseCurve.TAN])),
                base_amplitude
            ))
        if features & BaseCurve.ARC_SIN:
            y = concat_method(y, numpy.multiply(numpy.arcsin(numpy.add(x, base_phase)), base_amplitude))
        if features & BaseCurve.ARC_COS:
            y = concat_method(y, numpy.multiply(numpy.arccos(numpy.add(x, base_phase)), base_amplitude))
        if features & BaseCurve.ARC_TAN:
            y = concat_method(y, numpy.multiply(numpy.arctan(numpy.add(x, base_phase)), base_amplitude))
        if features & BaseCurve.SAWTOOTH:
            # TODO sawtooth config, also include option for repeats/speed until 360 (180 = 2)
            y = concat_method(y, numpy.multiply(numpy.mod(numpy.add(y, base_phase), 180.0), base_amplitude))
        if features & BaseCurve.RECT:
            pulse_width = 180
            ya = numpy.zeros(steps, dtype=numpy.float32)
            for i in range(int(base_phase * steps / pulse_width), steps, pulse_width):
                ya[i:i+pulse_width] = 1.0
            y = concat_method(y, numpy.multiply(ya, base_amplitude))
        if features & BaseCurve.TRIANGLE:
            # TODO triangle wave config
            pulse_width = 180
            ya = numpy.zeros(steps, dtype=numpy.float32)
            signal = numpy.mod(numpy.add(y, base_phase), pulse_width)
            for i in range(0, steps, pulse_width * 2):
                ya[i:i+pulse_width] = signal[i:i+pulse_width]
                ya[i+pulse_width+1:i+pulse_width*2] = numpy.subtract(1, signal[i+pulse_width+1:i+pulse_width*2])
            y = concat_method(y, numpy.multiply(ya, base_amplitude))
        try:
            self.setYRange(numpy.max(y)*1.5, numpy.min(y) * 1.5)
        except Exception as e:
            logger.exception(e)
        self._data_line.setData(x, y)

    @property
    def curve_config(self) -> CurveConfiguration:
        return self._curve_configuration

    @curve_config.setter
    def curve_config(self, new_config: CurveConfiguration):
        self._curve_configuration = new_config
        self.replot()


class CurveEditorWidget(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._config: CurveConfiguration = CurveConfiguration()
        self._loading_values: bool = False
        layout = QVBoxLayout()

        self._renderer = _WaveRenderer(self)
        layout.addWidget(self._renderer)
        self._concat_add_radiobutton = QRadioButton("Add Features", self)
        self._concat_add_radiobutton.toggled.connect(self._update_values_from_gui)
        layout.addWidget(self._concat_add_radiobutton)
        self._concat_mult_radiobutton = QRadioButton("Multiply Features", self)
        self._concat_mult_radiobutton.toggled.connect(self._update_values_from_gui)
        layout.addWidget(self._concat_mult_radiobutton)
        self._base_amplitude_edit = QDoubleSpinBox(self)
        self._base_amplitude_edit.valueChanged.connect(self._update_values_from_gui)
        layout.addWidget(QLabel("Amplitude:"))
        layout.addWidget(self._base_amplitude_edit)
        self._base_phase_edit = QDoubleSpinBox(self)
        self._base_phase_edit.valueChanged.connect(self._update_values_from_gui)
        layout.addWidget(QLabel("Phase:"))
        layout.addWidget(self._base_phase_edit)
        self._function_property_container = QTabWidget(self)  # TODO change this to fold down based on enablement select
        layout.addWidget(self._function_property_container)

        self._enabled_checkboxes: dict[str, QCheckBox] = {}
        self._frequency_dials: dict[str, QDoubleSpinBox] = {}

        for curve_name in [str(BaseCurve(2**c).name) for c in range(9)]:
            curve_widget = QWidget(self._function_property_container)
            c_layout = QFormLayout()
            self._enabled_checkboxes[curve_name] = QCheckBox(curve_widget)
            self._enabled_checkboxes[curve_name].stateChanged.connect(self._update_values_from_gui)
            c_layout.addRow("Enabled", self._enabled_checkboxes[curve_name])
            self._frequency_dials[curve_name] = QDoubleSpinBox(curve_widget)
            self._frequency_dials[curve_name].valueChanged.connect(self._update_values_from_gui)
            c_layout.addRow("Frequency", self._frequency_dials[curve_name])
            curve_widget.setLayout(c_layout)
            self._function_property_container.addTab(curve_widget, curve_name)

        self.setLayout(layout)

    def _load_values_from_config(self):
        self._loading_values = True
        self._base_amplitude_edit.setValue(self._config.base_amplitude)
        self._base_phase_edit.setValue(self._config.base_phase)
        self._concat_add_radiobutton.setChecked(self._config.append_features_using_addition)
        self._concat_mult_radiobutton.setChecked(not self._config.append_features_using_addition)
        for curve in [BaseCurve(2 ** c) for c in range(9)]:
            self._enabled_checkboxes[str(curve.name)].setChecked(self._config.selected_features & curve > 0)
            self._frequency_dials[str(curve.name)].setValue(self._config.frequencies[curve])
        self._loading_values = False

    def set_wave_config(self, wc: CurveConfiguration):
        self._config = wc
        self._load_values_from_config()
        self._renderer.curve_config = wc

    def _update_values_from_gui(self):
        if self._loading_values:
            return
        self._config.base_phase = self._base_phase_edit.value()
        self._config.base_amplitude = self._base_amplitude_edit.value()
        self._config.append_features_using_addition = self._concat_add_radiobutton.isChecked()
        selected_elements = BaseCurve.NONE
        for curve in [BaseCurve(2 ** c) for c in range(9)]:
            if self._enabled_checkboxes[str(curve.name)].isChecked():
                selected_elements |= curve
            self._config.frequencies[curve] = self._frequency_dials[str(curve.name)].value()
        self._config.selected_features = selected_elements
        # TODO copy values from GUI elements to config
        self._renderer.curve_config = self._config
        self._renderer.replot()
