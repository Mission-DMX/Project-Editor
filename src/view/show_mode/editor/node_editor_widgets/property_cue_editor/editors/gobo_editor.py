"""Gobo property editor (single-wheel for now)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QComboBox, QFormLayout, QVBoxLayout, QWidget

from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


_SLOT_OPTIONS = tuple((f"Slot {i}", i) for i in range(16))


class GoboEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "gobo", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self._wheel_count = 1
        self._goboslot = QComboBox()
        for label, val in _SLOT_OPTIONS:
            self._goboslot.addItem(label, val)
        self._goborotation = JogwheelDoubleSpinBox()
        self._goborotation.setRange(-100.0, 100.0)
        self._goborotation.setDecimals(4)
        form.addRow("Slot", self._goboslot)
        form.addRow("Rotation", self._goborotation)
        layout.addLayout(form)

    def _manual_values(self) -> dict[str, Any]:
        return {
            "wheel_count": int(self._wheel_count),
            "slots": {0: int(self._goboslot.currentData())},
            "rotations": {0: float(self._goborotation.value())},
        }

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        slots = values.get("slots", {})
        if isinstance(slots, dict):
            want = int(slots.get(0, 0))
            for i in range(self._goboslot.count()):
                if self._goboslot.itemData(i) == want:
                    self._goboslot.setCurrentIndex(i)
                    break
        rotations = values.get("rotations", {})
        if isinstance(rotations, dict):
            self._goborotation.setValue(float(rotations.get(0, 0.0)))
