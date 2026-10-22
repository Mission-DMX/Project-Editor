"""Editor for step-level attributes (name, duration, fade-in)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.model.property_step import PropertyStep


class StepEditor(QWidget):
    """Editor for the step row (first column of the tree)."""

    applied = Signal()

    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = model
        self._cue_index = 0
        self._step_index = 0

        layout = QVBoxLayout()
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._duration = JogwheelSpinBox()
        self._duration.setRange(1, 10_000_000)
        self._duration.setValue(40)
        self._fade_in = JogwheelSpinBox()
        self._fade_in.setRange(0, 10_000_000)
        form.addRow("Name", self._name_edit)
        form.addRow("Duration (40 Hz)", self._duration)
        form.addRow("Fade-in (40 Hz)", self._fade_in)
        layout.addLayout(form)
        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self._on_apply)
        layout.addWidget(self._apply_button)
        self.setLayout(layout)

    def load(self, cue_index: int, step_index: int) -> None:
        self._cue_index = cue_index
        self._step_index = step_index
        step = self._current_step()
        if step is None:
            self._name_edit.setText("")
            self._duration.setValue(40)
            self._fade_in.setValue(0)
            return
        self._name_edit.setText(step.name)
        self._duration.setValue(step.duration_40hz)
        self._fade_in.setValue(step.fade_in_40hz)

    def _current_step(self) -> PropertyStep | None:
        if self._cue_index < 0 or self._cue_index >= len(self._model.cues):
            return None
        cue = self._model.cues[self._cue_index]
        if self._step_index < 0 or self._step_index >= len(cue.steps):
            return None
        return cue.steps[self._step_index]

    def _on_apply(self) -> None:
        step = self._current_step()
        if step is None:
            return
        step.name = self._name_edit.text()
        step.duration_40hz = int(self._duration.value())
        step.fade_in_40hz = int(self._fade_in.value())
        self.applied.emit()
