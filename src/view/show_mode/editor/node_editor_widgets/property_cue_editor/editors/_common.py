"""Shared helpers for the per-property editors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QRadioButton,
    QWidget,
)

if TYPE_CHECKING:
    from PySide6.QtCore import SignalInstance

from model.virtual_filters.property_cues.distribution import Distribution, DistributionMethod
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox


class DistributionControls(QGroupBox):
    """Distribution method + numeric parameters group."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Distribution", parent)
        layout = QFormLayout()
        self._method = QComboBox()
        for m in DistributionMethod:
            self._method.addItem(m.value, m)
        self._phase_offset = JogwheelDoubleSpinBox()
        self._phase_offset.setRange(-1000.0, 1000.0)
        self._phase_offset.setDecimals(4)
        self._amplitude = JogwheelDoubleSpinBox()
        self._amplitude.setRange(-1000.0, 1000.0)
        self._amplitude.setDecimals(4)
        self._amplitude.setValue(1.0)
        self._introduction_only = QCheckBox("Introduction delay only")
        layout.addRow("Method", self._method)
        layout.addRow("Phase offset", self._phase_offset)
        layout.addRow("Amplitude", self._amplitude)
        layout.addRow("", self._introduction_only)
        self.setLayout(layout)

    def set_distribution(self, dist: Distribution) -> None:
        for i in range(self._method.count()):
            if self._method.itemData(i) == dist.method:
                self._method.setCurrentIndex(i)
                break
        self._phase_offset.setValue(dist.phase_offset)
        self._amplitude.setValue(dist.amplitude)
        self._introduction_only.setChecked(dist.introduction_delay_only)

    def distribution(self) -> Distribution:
        method = self._method.currentData() or DistributionMethod.CONSTANT
        return Distribution(
            method=method,
            phase_offset=float(self._phase_offset.value()),
            amplitude=float(self._amplitude.value()),
            introduction_delay_only=self._introduction_only.isChecked(),
        )


class ModeToggle(QGroupBox):
    """Radio button pair for manual vs preset mode."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Mode", parent)
        from PySide6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout()
        self._manual = QRadioButton("Manual")
        self._preset = QRadioButton("Preset")
        self._manual.setChecked(True)
        self._group = QButtonGroup(self)
        self._group.addButton(self._manual, 0)
        self._group.addButton(self._preset, 1)
        layout.addWidget(self._manual)
        layout.addWidget(self._preset)
        self.setLayout(layout)

    @property
    def is_manual(self) -> bool:
        return self._manual.isChecked()

    def set_manual(self, manual: bool) -> None:
        if manual:
            self._manual.setChecked(True)
        else:
            self._preset.setChecked(True)

    @property
    def toggled_signal(self) -> SignalInstance:
        return self._manual.toggled
