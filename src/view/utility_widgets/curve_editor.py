# coding=utf-8
"""This file contains a widget that allows the editing and visualization of parameters of a trigonometric curve."""

import numpy

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from typing import TYPE_CHECKING

from pyqtgraph import PlotWidget

from model.curve_configuration import CurveConfiguration, BaseCurve

if TYPE_CHECKING:
    pass


class _WaveRenderer(PlotWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self._curve_configuration: CurveConfiguration = CurveConfiguration()
        self._data_line = self.plotItem

    def _replot(self):
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
            x = concat_method(x, numpy.multiply(numpy.sin(numpy.add(y, base_phase)), base_amplitude))
            # TODO implement sin config
        if features & BaseCurve.COS:
            x = concat_method(x, numpy.multiply(numpy.cos(numpy.add(y, base_phase)), base_amplitude))
            # TODO implement cos config
        if features & BaseCurve.TAN:
            # TODO tan config
            x = concat_method(x, numpy.multiply(numpy.tan(numpy.add(y, base_phase)), base_amplitude))
        if features & BaseCurve.ARC_SIN:
            x = concat_method(x, numpy.multiply(numpy.arcsin(numpy.add(y, base_phase)), base_amplitude))
        if features & BaseCurve.ARC_COS:
            x = concat_method(x, numpy.multiply(numpy.arccos(numpy.add(y, base_phase)), base_amplitude))
        if features & BaseCurve.ARC_TAN:
            x = concat_method(x, numpy.multiply(numpy.arctan(numpy.add(y, base_phase)), base_amplitude))
        if features & BaseCurve.SAWTOOTH:
            # TODO sawtooth config, also include option for repeats/speed until 360 (180 = 2)
            x = concat_method(x, numpy.multiply(numpy.mod(numpy.add(y, base_phase), 180.0), base_amplitude))
        if features & BaseCurve.RECT:
            pulse_width = 180
            xa = numpy.zeros(steps, dtype=numpy.float32)
            for i in range(int(base_phase * steps / pulse_width), steps, pulse_width):
                xa[i:i+pulse_width] = 1.0
            x = concat_method(x, numpy.multiply(xa, base_amplitude))
        if features & BaseCurve.TRIANGLE:
            # TODO triangle wave config
            pulse_width = 180
            xa = numpy.zeros(steps, dtype=numpy.float32)
            signal = numpy.mod(numpy.add(y, base_phase), pulse_width)
            for i in range(0, steps, pulse_width * 2):
                xa[i:i+pulse_width] = signal[i:i+pulse_width]
                xa[i+pulse_width+1:i+pulse_width*2] = numpy.subtract(1, signal[i+pulse_width+1:i+pulse_width*2])
            x = concat_method(x, numpy.multiply(xa, base_amplitude))

class CurveEditorWidget(QWidget):

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        layout = QVBoxLayout()

        self._renderer = _WaveRenderer(self)
        layout.addWidget(self._renderer)
        self._function_property_container = QTabWidget(self)  # TODO change this to fold down based on enablement select
        layout.addWidget(self._function_property_container)

        self.setLayout(layout)
