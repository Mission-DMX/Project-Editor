"""Right-hand editor pane that switches per (step, node, property) selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QStackedWidget, QWidget

from .editors.beam_editor import BeamEditor
from .editors.colour_editor import ColourEditor
from .editors.dimmer_editor import DimmerEditor
from .editors.focus_editor import FocusEditor
from .editors.frost_editor import FrostEditor
from .editors.gobo_editor import GoboEditor
from .editors.position_editor import PositionEditor
from .editors.step_editor import StepEditor

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class PropertyPane(QStackedWidget):
    """Shows the editor matching the currently-selected (step, node, property)."""

    assignment_applied = Signal()

    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = model
        self._cue_index: int = 0

        self._placeholder = QLabel("Select a step or property in the tree.")
        self._placeholder.setWordWrap(True)
        self.addWidget(self._placeholder)

        self._step_editor = StepEditor(model)
        self.addWidget(self._step_editor)

        self._editors: dict[str, QWidget] = {
            "dimmer": DimmerEditor(model),
            "position": PositionEditor(model),
            "colour": ColourEditor(model),
            "gobo": GoboEditor(model),
            "beam": BeamEditor(model),
            "focus": FocusEditor(model),
            "frost": FrostEditor(model),
        }
        for widget in self._editors.values():
            self.addWidget(widget)

        self._step_editor.applied.connect(self.assignment_applied.emit)
        for widget in self._editors.values():
            widget.applied.connect(self.assignment_applied.emit)

    def set_current_cue(self, cue_index: int) -> None:
        self._cue_index = cue_index

    def show_editor(self, step_index: int, node_path: str, property_id: str) -> None:
        if node_path == "" and property_id == "":
            self._step_editor.load(self._cue_index, step_index)
            self.setCurrentWidget(self._step_editor)
            return
        if property_id == "":
            self.setCurrentWidget(self._placeholder)
            return
        editor = self._editors.get(property_id)
        if editor is None:
            self.setCurrentWidget(self._placeholder)
            return
        editor.load(self._cue_index, step_index, node_path)
        self.setCurrentWidget(editor)

    def current_editor(self) -> QWidget:
        return self.currentWidget()
