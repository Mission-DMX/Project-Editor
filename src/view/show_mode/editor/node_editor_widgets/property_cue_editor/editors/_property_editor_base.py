"""Shared skeleton for per-property editors (manual + preset + distribution)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.model.property_step import (
    ManualPropertyAssignment,
    PresetPropertyAssignment,
    PropertyAssignments,
)

from ._common import DistributionControls, ModeToggle
from ._preset_panel import PresetPanel

_TRANSITION_LABELS: tuple[tuple[TransferFunction, str], ...] = (
    (TransferFunction.LINEAR, "Linear"),
    (TransferFunction.EDGE, "Edge (step)"),
    (TransferFunction.SIGMOIDAL, "Sigmoidal"),
    (TransferFunction.EASE_IN, "Ease in"),
    (TransferFunction.EASE_OUT, "Ease out"),
)

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.model.property_step import PropertyAssignment


class PropertyEditorBase(QWidget):
    """Base class providing the manual/preset/distribution/apply plumbing."""

    applied = Signal()

    def __init__(
        self,
        model: PropertyCueFilterModel,
        property_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._property_id = property_id
        self._cue_index: int = 0
        self._step_index: int = 0
        self._node_path: str = ""

        self._outer = QVBoxLayout()
        self._mode = ModeToggle()
        self._outer.addWidget(self._mode)

        self._stack = QStackedWidget()
        self._manual_widget = QWidget()
        self._manual_layout = QVBoxLayout()
        self._manual_widget.setLayout(self._manual_layout)
        self._stack.addWidget(self._manual_widget)

        self._preset_panel = PresetPanel(property_id)
        self._stack.addWidget(self._preset_panel)
        self._outer.addWidget(self._stack)

        self._distribution = DistributionControls()
        self._outer.addWidget(self._distribution)

        # L18: expose a transition selector so users can pick between linear,
        # sigmoidal, ease in/out and EDGE (hold-until-next-keyframe). The
        # compiler still forces EDGE for discrete channels (gobo slot, pan/
        # tilt curvesel, prism selection) per L26; this control affects the
        # continuous channels of the same property.
        transition_row = QHBoxLayout()
        transition_row.addWidget(QLabel("Transition"))
        self._transition_combo = QComboBox()
        for tf, label in _TRANSITION_LABELS:
            self._transition_combo.addItem(label, tf.value)
        self._transition_combo.setCurrentIndex(0)  # default linear
        transition_row.addWidget(self._transition_combo)
        transition_row.addStretch(1)
        self._outer.addLayout(transition_row)

        action_row = QHBoxLayout()
        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self._on_apply)
        action_row.addWidget(self._apply_button)
        # L9: an explicit "Remove assignment" action so the user can undo a
        # mis-authored property-pane value without re-running the wizard.
        self._remove_button = QPushButton("Remove assignment")
        self._remove_button.setToolTip(
            "Drop this (step, node, property) assignment so the fixture "
            "falls back to the compiler's default channel values.",
        )
        self._remove_button.clicked.connect(self._on_remove)
        action_row.addWidget(self._remove_button)
        self._outer.addLayout(action_row)
        self.setLayout(self._outer)

        self._mode.toggled_signal.connect(self._on_mode_toggle)
        self._install_manual_widgets(self._manual_layout)

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        raise NotImplementedError

    def _manual_values(self) -> dict[str, Any]:
        raise NotImplementedError

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        raise NotImplementedError

    def _on_mode_toggle(self, manual: bool) -> None:
        self._stack.setCurrentIndex(0 if manual else 1)

    def load(self, cue_index: int, step_index: int, node_path: str) -> None:
        self._cue_index = cue_index
        self._step_index = step_index
        self._node_path = node_path
        assignment = self._current_assignment()
        if isinstance(assignment, PresetPropertyAssignment):
            self._mode.set_manual(False)
            self._stack.setCurrentIndex(1)
            self._preset_panel.set_selected_preset(assignment.preset_id, assignment.hint_values)
            self._distribution.set_distribution(assignment.distribution)
            # Preset-based assignments embed per-keyframe transitions in the
            # preset definition itself; default the picker to Linear.
            self._set_transition_combo(TransferFunction.LINEAR.value)
        elif isinstance(assignment, ManualPropertyAssignment):
            self._mode.set_manual(True)
            self._stack.setCurrentIndex(0)
            self._load_manual_values(assignment.values)
            self._distribution.set_distribution(assignment.distribution)
            self._set_transition_combo(assignment.transition)
        else:
            # L17: no assignment exists at the new (cue, step, node) selection.
            # Reset the manual widgets to their spec defaults and the
            # distribution controls to CONSTANT so the previous node's state
            # doesn't leak through visually.
            self._mode.set_manual(True)
            self._stack.setCurrentIndex(0)
            self._load_manual_values({})
            from model.virtual_filters.property_cues.distribution import Distribution
            self._distribution.set_distribution(Distribution())
            self._set_transition_combo(TransferFunction.LINEAR.value)

    def _set_transition_combo(self, transition_value: str) -> None:
        """Select the combo entry whose userData matches ``transition_value``."""
        idx = self._transition_combo.findData(transition_value)
        if idx < 0:
            idx = 0
        self._transition_combo.setCurrentIndex(idx)

    def _current_transition_value(self) -> str:
        """Return the TransferFunction string value (e.g. ``"lin"``) from the combo."""
        value = self._transition_combo.currentData()
        if isinstance(value, str) and value:
            return value
        return TransferFunction.LINEAR.value

    def _current_assignment(self) -> PropertyAssignment | None:
        if self._cue_index < 0 or self._cue_index >= len(self._model.cues):
            return None
        cue = self._model.cues[self._cue_index]
        if self._step_index < 0 or self._step_index >= len(cue.steps):
            return None
        step = cue.steps[self._step_index]
        bucket = step.assignments.get(self._node_path)
        if bucket is None:
            return None
        return bucket.by_property.get(self._property_id)

    def _ensure_bucket(self) -> PropertyAssignments | None:
        """Return the assignments bucket for the current (step, node) selection.

        ``self._node_path == ""`` represents a step-level assignment that applies to
        every selected child; the compiler expands it in :func:`_resolve_path_children`.
        """
        if self._cue_index < 0 or self._cue_index >= len(self._model.cues):
            return None
        cue = self._model.cues[self._cue_index]
        if self._step_index < 0 or self._step_index >= len(cue.steps):
            return None
        step = cue.steps[self._step_index]
        bucket = step.assignments.get(self._node_path)
        if bucket is None:
            bucket = PropertyAssignments()
            step.assignments[self._node_path] = bucket
        return bucket

    def _on_apply(self) -> None:
        bucket = self._ensure_bucket()
        if bucket is None:
            return
        distribution = self._distribution.distribution()
        if self._mode.is_manual:
            assignment = ManualPropertyAssignment(
                values=self._manual_values(),
                distribution=distribution,
                transition=self._current_transition_value(),
            )
        else:
            preset_name = self._preset_panel.selected_preset_name()
            if preset_name is None:
                return
            assignment = PresetPropertyAssignment(
                preset_id=preset_name,
                hint_values=self._preset_panel.hint_values(),
                distribution=distribution,
            )
        bucket.by_property[self._property_id] = assignment
        self.applied.emit()

    def _on_remove(self) -> None:
        """L9: pop this property's assignment from the current (step, node) bucket.

        No-op if no assignment exists. Empty assignment buckets are left
        behind — the compiler ignores them, and keeping them lets the user
        re-apply the same node_path without the bucket having to be
        recreated.
        """
        if self._cue_index < 0 or self._cue_index >= len(self._model.cues):
            return
        cue = self._model.cues[self._cue_index]
        if self._step_index < 0 or self._step_index >= len(cue.steps):
            return
        step = cue.steps[self._step_index]
        bucket = step.assignments.get(self._node_path)
        if bucket is None:
            return
        if bucket.by_property.pop(self._property_id, None) is None:
            return
        # Reset the editor's widgets so what remains on screen matches the
        # now-empty assignment.
        self._load_manual_values({})
        from model.virtual_filters.property_cues.distribution import Distribution
        self._distribution.set_distribution(Distribution())
        self.applied.emit()
