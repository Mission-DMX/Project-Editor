"""Frost property editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class FrostEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "frost", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self._frost = JogwheelSpinBox()
        self._frost.setRange(0, 255)
        form.addRow("Frost intensity", self._frost)
        layout.addLayout(form)

    def _manual_values(self) -> dict[str, Any]:
        return {"frost_intensity": int(self._frost.value())}

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        self._frost.setValue(int(values.get("frost_intensity", 0)))
