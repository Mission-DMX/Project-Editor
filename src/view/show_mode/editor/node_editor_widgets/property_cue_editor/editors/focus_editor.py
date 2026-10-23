"""Focus-only editor (writes to a dedicated 'focus' property slot)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class FocusEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "focus", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        form = QFormLayout()
        self._focus = JogwheelSpinBox()
        self._focus.setRange(0, 255)
        form.addRow("Focus", self._focus)
        layout.addLayout(form)

    def _manual_values(self) -> dict[str, Any]:
        return {"focus": int(self._focus.value())}

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        self._focus.setValue(int(values.get("focus", 0)))
