"""Preset selection + hint-value form shared by property editors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QWidget,
)

from model.virtual_filters.property_cues.presets.loader import load_preset_library
from model.virtual_filters.property_cues.presets.model import PresetHintType
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox, JogwheelSpinBox

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.presets.model import EffectPreset


class PresetPanel(QGroupBox):
    """Dropdown of presets whose ``applies_for`` matches, plus a hint-value form."""

    def __init__(
        self,
        property_id: str,
        parent: QWidget | None = None,
        library: dict[str, EffectPreset] | None = None,
    ) -> None:
        super().__init__("Preset", parent)
        self._property_id = property_id
        self._library: dict[str, EffectPreset] = library if library is not None else self._load_safe_library()
        self._filtered: list[EffectPreset] = [
            p for p in self._library.values() if p.applies_for == property_id
        ]
        layout = QFormLayout()
        self._combo = QComboBox()
        self._combo.addItem("", None)
        for preset in self._filtered:
            self._combo.addItem(preset.name, preset)
        self._combo.currentIndexChanged.connect(self._rebuild_hints)
        layout.addRow("Preset", self._combo)
        self._hints_container = QWidget()
        self._hints_layout = QFormLayout()
        self._hints_container.setLayout(self._hints_layout)
        self._hint_widgets: dict[str, QWidget] = {}
        layout.addRow(self._hints_container)
        self.setLayout(layout)

    @staticmethod
    def _load_safe_library() -> dict[str, EffectPreset]:
        try:
            return load_preset_library()
        except Exception:
            return {}

    def set_library(self, library: dict[str, EffectPreset]) -> None:
        self._library = library
        self._filtered = [p for p in self._library.values() if p.applies_for == self._property_id]
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("", None)
        for preset in self._filtered:
            self._combo.addItem(preset.name, preset)
        self._combo.blockSignals(False)
        self._rebuild_hints()

    def _rebuild_hints(self) -> None:
        while self._hints_layout.rowCount():
            self._hints_layout.removeRow(0)
        self._hint_widgets = {}
        preset = self._combo.currentData()
        if preset is None:
            return
        for hint in preset.hints:
            widget = self._build_hint_widget(hint)
            self._hint_widgets[hint.id] = widget
            self._hints_layout.addRow(hint.id, widget)

    def _build_hint_widget(self, hint: Any) -> QWidget:
        if hint.type is PresetHintType.FLOAT:
            w = JogwheelDoubleSpinBox()
            w.setDecimals(4)
            lo = hint.minimum if hint.minimum is not None else -1_000_000.0
            hi = hint.maximum if hint.maximum is not None else 1_000_000.0
            w.setRange(lo, hi)
            try:
                w.setValue(float(hint.default))
            except (TypeError, ValueError):
                pass
            return w
        if hint.type is PresetHintType.INT:
            w2 = JogwheelSpinBox()
            lo_i = int(hint.minimum) if hint.minimum is not None else -1_000_000
            hi_i = int(hint.maximum) if hint.maximum is not None else 1_000_000
            w2.setRange(lo_i, hi_i)
            try:
                w2.setValue(int(hint.default))
            except (TypeError, ValueError):
                pass
            return w2
        line = QLineEdit()
        line.setText(str(hint.default))
        return line

    def selected_preset_name(self) -> str | None:
        preset = self._combo.currentData()
        return preset.name if preset is not None else None

    def hint_values(self) -> dict[str, Any]:
        preset = self._combo.currentData()
        if preset is None:
            return {}
        out: dict[str, Any] = {}
        for hint in preset.hints:
            widget = self._hint_widgets.get(hint.id)
            if widget is None:
                continue
            if isinstance(widget, (JogwheelDoubleSpinBox, JogwheelSpinBox)):
                out[hint.id] = widget.value()
            elif isinstance(widget, QLineEdit):
                out[hint.id] = widget.text()
        return out

    def set_selected_preset(self, name: str) -> None:
        for i in range(self._combo.count()):
            preset = self._combo.itemData(i)
            if preset is not None and preset.name == name:
                self._combo.setCurrentIndex(i)
                return
