"""Colour property editor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from model.color_hsi import ColorHSI

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class ColourEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "colour", parent)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        self._current_colour: ColorHSI = ColorHSI(0.0, 0.0, 0.0)
        row = QHBoxLayout()
        self._preview = QLabel("")
        self._preview.setMinimumWidth(60)
        self._preview.setAutoFillBackground(True)
        self._pick_button = QPushButton("Pick colour...")
        self._pick_button.clicked.connect(self._on_pick)
        row.addWidget(self._preview)
        row.addWidget(self._pick_button)
        layout.addLayout(row)
        self._update_preview()

    def _on_pick(self) -> None:
        current = self._current_colour.to_qt_color()
        picked = QColorDialog.getColor(current, self, "Pick colour")
        if not picked.isValid():
            return
        self._current_colour = ColorHSI.from_qt_color(picked)
        self._update_preview()

    def _update_preview(self) -> None:
        r, g, b = self._current_colour.to_rgb()
        self._preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b});")

    def _manual_values(self) -> dict[str, Any]:
        return {"color": self._current_colour.copy()}

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        colour = values.get("color")
        if isinstance(colour, ColorHSI):
            self._current_colour = colour.copy()
        self._update_preview()
