"""Shared skeleton for per-property editors (manual + preset + distribution)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from model.virtual_filters.property_cues.model.property_step import (
    ManualPropertyAssignment,
    PresetPropertyAssignment,
    PropertyAssignments,
)

from ._common import DistributionControls, ModeToggle
from ._preset_panel import PresetPanel

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

        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self._on_apply)
        self._outer.addWidget(self._apply_button)
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
            self._preset_panel.set_selected_preset(assignment.preset_id)
            self._distribution.set_distribution(assignment.distribution)
        elif isinstance(assignment, ManualPropertyAssignment):
            self._mode.set_manual(True)
            self._stack.setCurrentIndex(0)
            self._load_manual_values(assignment.values)
            self._distribution.set_distribution(assignment.distribution)
        else:
            self._mode.set_manual(True)
            self._stack.setCurrentIndex(0)

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
        if self._cue_index < 0 or self._cue_index >= len(self._model.cues):
            return None
        cue = self._model.cues[self._cue_index]
        if self._step_index < 0 or self._step_index >= len(cue.steps):
            return None
        step = cue.steps[self._step_index]
        if self._node_path == "":
            return None
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
