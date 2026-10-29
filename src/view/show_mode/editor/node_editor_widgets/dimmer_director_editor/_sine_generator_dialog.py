"""Modal dialog that generates a seamless-loop sine sample list for an effect curve."""

from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

_TICK_PERIOD_MS = 25
"""Fish update tick period (40 Hz). Must match the dimmer_director model constant."""


class SineGeneratorDialog(QDialog):
    """Dialog collecting sine-wave parameters and producing the sample list.

    The generated sample list covers exactly one period of the configured frequency so
    that continuous looping on fish feels like a continuous wave: the last tick lines up
    with the first. Values outside ``[0, 1]`` are clamped at generation time.

    Defaults produce a 3 s sine wave (frequency ≈ 0.333 Hz, one period = 3 s) oscillating
    between 0 and 1 (amplitude 0.5, offset 0.5) with no phase offset.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the four spin-box form and the OK/Cancel buttons."""
        super().__init__(parent)
        self.setWindowTitle("Generate sine effect curve")
        self.setModal(True)
        layout = QVBoxLayout()
        intro = QLabel(
            "Generate a sine wave covering exactly one period so looping feels seamless. "
            "Samples outside [0, 1] are clamped.",
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        self._amplitude_sb = JogwheelDoubleSpinBox()
        self._amplitude_sb.setRange(0.0, 5.0)
        self._amplitude_sb.setDecimals(4)
        self._amplitude_sb.setSingleStep(0.05)
        self._amplitude_sb.setValue(0.5)
        form.addRow("Amplitude:", self._amplitude_sb)

        self._offset_sb = JogwheelDoubleSpinBox()
        self._offset_sb.setRange(-5.0, 5.0)
        self._offset_sb.setDecimals(4)
        self._offset_sb.setSingleStep(0.05)
        self._offset_sb.setValue(0.5)
        form.addRow("Offset:", self._offset_sb)

        self._frequency_sb = JogwheelDoubleSpinBox()
        self._frequency_sb.setRange(0.01, 20.0)
        self._frequency_sb.setDecimals(4)
        self._frequency_sb.setSingleStep(0.1)
        self._frequency_sb.setValue(1.0 / 3.0)
        self._frequency_sb.setSuffix(" Hz")
        form.addRow("Frequency:", self._frequency_sb)

        self._phase_sb = JogwheelDoubleSpinBox()
        self._phase_sb.setRange(-360.0, 360.0)
        self._phase_sb.setDecimals(2)
        self._phase_sb.setSingleStep(5.0)
        self._phase_sb.setValue(0.0)
        self._phase_sb.setSuffix(" °")
        form.addRow("Phase:", self._phase_sb)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        hint = self.sizeHint()
        self.setMinimumSize(int(hint.width() * 1.5), int(hint.height() * 1.5))

    def generate_samples(self) -> list[float]:
        """Return the generated sample list for the currently entered parameters."""
        amplitude = float(self._amplitude_sb.value())
        offset = float(self._offset_sb.value())
        frequency = max(0.0001, float(self._frequency_sb.value()))
        phase_rad = math.radians(float(self._phase_sb.value()))
        period_s = 1.0 / frequency
        tick_count = max(2, round(period_s * 1000.0 / _TICK_PERIOD_MS))
        samples: list[float] = []
        for i in range(tick_count):
            t = i / tick_count  # normalized position within the period
            value = offset + amplitude * math.sin(2.0 * math.pi * t + phase_rad)
            samples.append(max(0.0, min(1.0, value)))
        return samples
