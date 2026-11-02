"""Beam property editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox, JogwheelSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class BeamEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "beam", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self._zoom = JogwheelSpinBox()
        self._zoom.setRange(0, 255)
        self._prism_sel = JogwheelSpinBox()
        self._prism_sel.setRange(0, 255)
        self._prism_rot = JogwheelDoubleSpinBox()
        self._prism_rot.setRange(-100.0, 100.0)
        self._prism_rot.setDecimals(4)
        self._iris = JogwheelSpinBox()
        self._iris.setRange(0, 255)
        form.addRow("Zoom", self._zoom)
        form.addRow("Prism selection", self._prism_sel)
        form.addRow("Prism rotation", self._prism_rot)
        form.addRow("Iris", self._iris)
        layout.addLayout(form)

    def _manual_values(self) -> dict[str, Any]:
        return {
            "zoom": int(self._zoom.value()),
            "prism_selection": int(self._prism_sel.value()),
            "prism_rotation": float(self._prism_rot.value()),
            "iris": int(self._iris.value()),
        }

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        self._zoom.setValue(int(values.get("zoom", 0)))
        self._prism_sel.setValue(int(values.get("prism_selection", 0)))
        self._prism_rot.setValue(float(values.get("prism_rotation", 0.0)))
        self._iris.setValue(int(values.get("iris", 0)))
