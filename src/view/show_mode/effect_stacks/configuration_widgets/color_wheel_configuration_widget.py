"""This file contains the configuration widget for the color wheel effect."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QSpinBox, QWidget

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.effects.color_effects import ColorWheelEffect


class ColorWheelConfigurationWidget(QWidget):
    """This widget enables the user to set up the defaults of the color wheel effect settings."""

    def __init__(self, f: ColorWheelEffect):
        super().__init__()
        self._f: ColorWheelEffect = f
        layout = QFormLayout()
        self.setLayout(layout)

        self._fragment_number_widget = QSpinBox(self)
        self._fragment_number_widget.setMinimum(1)
        self._fragment_number_widget.valueChanged.connect(self._fragment_count_changed)
        layout.addRow("Number of Fragments", self._fragment_number_widget)
        self._minimum_hue = QDoubleSpinBox(self)
        self._minimum_hue.setMinimum(0)
        self._minimum_hue.setMaximum(360)
        self._minimum_hue.valueChanged.connect(self._min_hue_changed)
        layout.addRow("Minimum Hue", self._minimum_hue)
        self._maximum_hue = QDoubleSpinBox(self)
        self._maximum_hue.setMinimum(0)
        self._maximum_hue.setMaximum(360)
        self._maximum_hue.valueChanged.connect(self._max_hue_changed)
        layout.addRow("Maximum Hue", self._maximum_hue)
        # TODO add color to hue indicator
        # TODO add default speed widget
        # TODO disable settings if the corresponding input is occupied
        self.load_values_from_effect()

    def _fragment_count_changed(self, e):
        self._f.fragment_number = self._fragment_number_widget.value()

    def _min_hue_changed(self, e):
        self._f.min_hue = self._minimum_hue.value()

    def _max_hue_changed(self, e):
        self._f.max_hue = self._maximum_hue.value()

    def load_values_from_effect(self):
        self._fragment_number_widget.setValue(self._f.fragment_number)
        self._minimum_hue.setValue(self._f.min_hue)
        self._maximum_hue.setValue(self._f.max_hue)

    def setVisible(self, visible):
        self.load_values_from_effect()
        return super().setVisible(visible)
