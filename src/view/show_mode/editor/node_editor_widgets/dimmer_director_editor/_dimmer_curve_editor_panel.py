"""Dimmer curve editor panel: type selector + Bézier params + response preview."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from model.filters.dimmer_director import DimmerCurveType
from view.show_mode.editor.node_editor_widgets.dimmer_director_editor._sample_preview import DimmerResponsePreview

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerCurve, DimmerDirectorFilter


_BEZIER_DEFAULTS: list[float] = [0.0, 0.0, 1.0, 1.0]


class DimmerCurveEditorPanel(QWidget):
    """Edit one dimmer curve: pick type / Bézier params and preview the response."""

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout. Empty until ``set_curve_index`` is called."""
        super().__init__(parent)
        self._model = model
        self._curve_index: int | None = None
        self._applying = False
        layout = QVBoxLayout()
        self._header_label = QLabel("No dimmer curve selected")
        layout.addWidget(self._header_label)

        form = QFormLayout()
        self._type_combo = QComboBox()
        for ct in DimmerCurveType:
            self._type_combo.addItem(ct.value, ct)
        self._type_combo.currentIndexChanged.connect(self._type_changed)
        form.addRow("Curve type:", self._type_combo)

        self._bezier_row = QWidget()
        bezier_layout = QHBoxLayout()
        bezier_layout.setContentsMargins(0, 0, 0, 0)
        self._bezier_spins: list[QDoubleSpinBox] = []
        for i in range(4):
            sb = QDoubleSpinBox()
            sb.setRange(-10.0, 10.0)
            sb.setSingleStep(0.05)
            sb.setDecimals(3)
            sb.setValue(_BEZIER_DEFAULTS[i])
            sb.valueChanged.connect(self._bezier_param_changed)
            bezier_layout.addWidget(QLabel(f"p{i}"))
            bezier_layout.addWidget(sb)
            self._bezier_spins.append(sb)
        bezier_layout.addStretch()
        self._bezier_row.setLayout(bezier_layout)
        form.addRow("Bézier y:", self._bezier_row)
        layout.addLayout(form)

        self._preview = DimmerResponsePreview()
        layout.addWidget(self._preview, 1)
        self.setLayout(layout)

        self._model.configuration_changed.mapped_signal.connect(self._refresh)

    def set_curve_index(self, index: int | None) -> None:
        """Switch the panel to display the dimmer curve at ``index``."""
        self._curve_index = index
        self._refresh()

    def _current_curve(self) -> DimmerCurve | None:
        if self._curve_index is None:
            return None
        curves = self._model.dimmer_curves
        if not 0 <= self._curve_index < len(curves):
            return None
        return curves[self._curve_index]

    def _refresh(self) -> None:
        """Repopulate controls and preview from the current curve."""
        curve = self._current_curve()
        self._applying = True
        try:
            if curve is None:
                self._header_label.setText("No dimmer curve selected")
                self._type_combo.setEnabled(False)
                self._bezier_row.setEnabled(False)
                self._preview.set_curve(None)
                return
            self._header_label.setText(f"Editing dimmer curve '{curve.name}'")
            self._type_combo.setEnabled(True)
            type_index = self._type_combo.findData(curve.type)
            if type_index >= 0:
                self._type_combo.setCurrentIndex(type_index)
            is_bezier = curve.type == DimmerCurveType.BEZIER
            self._bezier_row.setEnabled(is_bezier)
            if is_bezier:
                params = curve.params if len(curve.params) >= 4 else _BEZIER_DEFAULTS
                for i, sb in enumerate(self._bezier_spins):
                    sb.setValue(params[i])
            self._preview.set_curve(curve)
        finally:
            self._applying = False

    def _type_changed(self, _: int) -> None:
        """Push the newly selected curve type into the model."""
        if self._applying:
            return
        curve = self._current_curve()
        if curve is None:
            return
        new_type = self._type_combo.currentData()
        if not isinstance(new_type, DimmerCurveType):
            return
        if curve.type == new_type:
            return
        curve.type = new_type
        if new_type == DimmerCurveType.BEZIER and len(curve.params) < 4:
            curve.params = list(_BEZIER_DEFAULTS)
        self._model.configuration_changed.mapped_signal.emit()

    def _bezier_param_changed(self, _: float) -> None:
        """Push the four Bézier spin box values into the model."""
        if self._applying:
            return
        curve = self._current_curve()
        if curve is None or curve.type != DimmerCurveType.BEZIER:
            return
        curve.params = [sb.value() for sb in self._bezier_spins]
        self._model.configuration_changed.mapped_signal.emit()
