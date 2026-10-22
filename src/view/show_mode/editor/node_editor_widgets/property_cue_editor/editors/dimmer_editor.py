"""Dimmer property editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class DimmerEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "dimmer", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self._brightness = JogwheelDoubleSpinBox()
        self._brightness.setRange(0.0, 1.0)
        self._brightness.setDecimals(4)
        self._brightness.setSingleStep(0.05)
        self._strobefreq = JogwheelDoubleSpinBox()
        self._strobefreq.setRange(0.0, 50.0)
        self._strobefreq.setDecimals(4)
        form.addRow("Brightness", self._brightness)
        form.addRow("Strobe (Hz)", self._strobefreq)
        layout.addLayout(form)

    def _manual_values(self) -> dict[str, Any]:
        return {
            "brightness": float(self._brightness.value()),
            "strobefreq": float(self._strobefreq.value()),
        }

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        self._brightness.setValue(float(values.get("brightness", 0.0)))
        self._strobefreq.setValue(float(values.get("strobefreq", 0.0)))
