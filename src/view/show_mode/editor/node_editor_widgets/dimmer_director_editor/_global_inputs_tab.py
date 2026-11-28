"""Tab for the Dimmer Director's global mixin/offset input counts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFormLayout, QLabel, QSpinBox, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerDirectorFilter


class GlobalInputsTab(QWidget):
    """Two spin boxes controlling the ``n_mix_global`` / ``n_off_global`` counts."""

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout and seed the spin boxes with the current model state."""
        super().__init__(parent)
        self._model = model
        layout = QVBoxLayout()
        form = QFormLayout()
        self._mixin_sb = QSpinBox()
        self._mixin_sb.setRange(0, 256)
        self._mixin_sb.setValue(model.global_mixin_count)
        self._mixin_sb.valueChanged.connect(self._mixin_changed)
        form.addRow("Global mixin inputs:", self._mixin_sb)
        self._offset_sb = QSpinBox()
        self._offset_sb.setRange(0, 256)
        self._offset_sb.setValue(model.global_offset_count)
        self._offset_sb.valueChanged.connect(self._offset_changed)
        form.addRow("Global offset inputs:", self._offset_sb)
        layout.addLayout(form)
        self._summary = QLabel()
        self._summary.setWordWrap(True)
        layout.addWidget(self._summary)
        layout.addStretch()
        self.setLayout(layout)
        self._refresh_summary()
        self._model.configuration_changed.mapped_signal.connect(self._refresh_summary)

    def _mixin_changed(self, value: int) -> None:
        """Push the new global mixin count into the model."""
        self._model.global_mixin_count = value

    def _offset_changed(self, value: int) -> None:
        """Push the new global offset count into the model."""
        self._model.global_offset_count = value

    def _refresh_summary(self) -> None:
        """Rebuild the "generated inputs" summary label."""
        mixin_names = ", ".join(f"mixin_{i}" for i in range(self._model.global_mixin_count)) or "none"
        offset_names = ", ".join(f"offset_{i}" for i in range(self._model.global_offset_count)) or "none"
        self._summary.setText(f"Mixin inputs: {mixin_names}\nOffset inputs: {offset_names}")
