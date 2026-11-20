"""Editor for step-level timings (name, duration, fade-in). Values are in seconds."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.model.property_step import PropertyStep


_TICKS_PER_SECOND = 40.0


class StepEditor(QWidget):
    """Edit the name, duration and fade-in of the selected step (seconds).

    All three fields auto-apply as soon as the user commits them (text
    editing-finished for the name, ``valueChanged`` for the spin boxes).
    The former Apply button was easy to miss -- users would set a duration,
    close the dialog, and find the step still at its default 1 s because the
    change had never been written to the model.
    """

    applied = Signal()

    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = model
        self._cue_index = 0
        self._step_index = 0
        self._loading = False

        layout = QVBoxLayout()
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._duration = JogwheelDoubleSpinBox()
        self._duration.setRange(0.025, 100000.0)
        self._duration.setDecimals(3)
        self._duration.setSingleStep(0.1)
        self._duration.setValue(1.0)
        self._fade_in = JogwheelDoubleSpinBox()
        self._fade_in.setRange(0.0, 100000.0)
        self._fade_in.setDecimals(3)
        self._fade_in.setSingleStep(0.1)
        form.addRow("Name", self._name_edit)
        form.addRow("Duration (s)", self._duration)
        form.addRow("Fade-in (s)", self._fade_in)
        layout.addLayout(form)
        self.setLayout(layout)

        self._name_edit.editingFinished.connect(self._persist)
        self._duration.valueChanged.connect(self._persist)
        self._fade_in.valueChanged.connect(self._persist)

    def load(self, cue_index: int, step_index: int) -> None:
        self._cue_index = cue_index
        self._step_index = step_index
        # Disable the auto-apply slot while we seed the widgets from the model
        # so the value-changed signals don't bounce the same values straight
        # back out as a spurious "user edit".
        self._loading = True
        try:
            step = self._current_step()
            if step is None:
                self._name_edit.setText("")
                self._duration.setValue(1.0)
                self._fade_in.setValue(0.0)
                return
            self._name_edit.setText(step.name)
            self._duration.setValue(step.duration_40hz / _TICKS_PER_SECOND)
            self._fade_in.setValue(step.fade_in_40hz / _TICKS_PER_SECOND)
        finally:
            self._loading = False

    def _current_step(self) -> PropertyStep | None:
        if self._cue_index < 0 or self._cue_index >= len(self._model.cues):
            return None
        cue = self._model.cues[self._cue_index]
        if self._step_index < 0 or self._step_index >= len(cue.steps):
            return None
        return cue.steps[self._step_index]

    def _persist(self) -> None:
        if self._loading:
            return
        step = self._current_step()
        if step is None:
            return
        step.name = self._name_edit.text()
        step.duration_40hz = max(1, round(self._duration.value() * _TICKS_PER_SECOND))
        step.fade_in_40hz = max(0, round(self._fade_in.value() * _TICKS_PER_SECOND))
        self.applied.emit()
