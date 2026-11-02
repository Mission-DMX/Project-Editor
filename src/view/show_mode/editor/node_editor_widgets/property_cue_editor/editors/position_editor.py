"""Position property editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QComboBox, QFormLayout, QVBoxLayout, QWidget

from model.virtual_filters.property_cues.properties.position import (
    CURVE_COS,
    CURVE_DIRECT,
    CURVE_SIN,
)
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


_CURVE_OPTIONS = (
    ("Direct", CURVE_DIRECT),
    ("Sin", CURVE_SIN),
    ("Cos", CURVE_COS),
)


def _curve_combo() -> QComboBox:
    c = QComboBox()
    for label, val in _CURVE_OPTIONS:
        c.addItem(label, val)
    return c


class PositionEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "position", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self._pan_value = JogwheelDoubleSpinBox()
        self._pan_value.setRange(-10_000.0, 10_000.0)
        self._pan_value.setDecimals(4)
        self._tilt_value = JogwheelDoubleSpinBox()
        self._tilt_value.setRange(-10_000.0, 10_000.0)
        self._tilt_value.setDecimals(4)
        self._pan_curve = _curve_combo()
        self._tilt_curve = _curve_combo()
        form.addRow("Pan value", self._pan_value)
        form.addRow("Pan curve", self._pan_curve)
        form.addRow("Tilt value", self._tilt_value)
        form.addRow("Tilt curve", self._tilt_curve)
        layout.addLayout(form)

    def _manual_values(self) -> dict[str, Any]:
        return {
            "pan_value": float(self._pan_value.value()),
            "pan_curvesel": int(self._pan_curve.currentData()),
            "tilt_value": float(self._tilt_value.value()),
            "tilt_curvesel": int(self._tilt_curve.currentData()),
        }

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        self._pan_value.setValue(float(values.get("pan_value", 0.0)))
        self._tilt_value.setValue(float(values.get("tilt_value", 0.0)))
        for combo, key in ((self._pan_curve, "pan_curvesel"), (self._tilt_curve, "tilt_curvesel")):
            want = int(values.get(key, CURVE_DIRECT))
            for i in range(combo.count()):
                if combo.itemData(i) == want:
                    combo.setCurrentIndex(i)
                    break
