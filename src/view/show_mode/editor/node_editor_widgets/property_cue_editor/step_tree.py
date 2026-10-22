"""Step / fixture / segment tree with per-property summary columns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from model.virtual_filters.property_cues.model.fixture_selection import SelectionEntryKind
from model.virtual_filters.property_cues.model.property_step import (
    ManualPropertyAssignment,
    PresetPropertyAssignment,
)

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.model.property_cue import PropertyCue
    from model.virtual_filters.property_cues.model.property_step import PropertyStep


_COLUMNS = ("Name / duration", "Fade-in", "Dimmer", "Position", "Gobo", "Colour", "Beam", "Focus")

_PROPERTY_COLUMNS: dict[int, str] = {
    2: "dimmer",
    3: "position",
    4: "gobo",
    5: "colour",
    6: "beam",
    7: "focus",
}

_ROLE_STEP_INDEX = Qt.ItemDataRole.UserRole + 1
_ROLE_NODE_PATH = Qt.ItemDataRole.UserRole + 2


def _fmt_time_40hz(ticks: int) -> str:
    seconds = ticks / 40.0
    return f"{seconds:.2f}s"


def _summary_for(property_id: str, assignment: object) -> str:
    if isinstance(assignment, PresetPropertyAssignment):
        return assignment.preset_id
    if isinstance(assignment, ManualPropertyAssignment):
        values = assignment.values
        if property_id == "dimmer":
            value = values.get("brightness", 0.0)
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                return "?"
        if property_id == "position":
            pan = values.get("pan_value", 0.0)
            tilt = values.get("tilt_value", 0.0)
            try:
                return f"{float(pan):.2f}/{float(tilt):.2f}"
            except (TypeError, ValueError):
                return "?"
        if property_id == "colour":
            colour = values.get("color")
            if colour is not None:
                return str(colour)
            return "set"
        if property_id == "gobo":
            slots = values.get("slots", {})
            if isinstance(slots, dict) and slots:
                return ",".join(str(v) for v in slots.values())
            return "0"
        if property_id == "beam":
            focus = values.get("focus", 0)
            return f"f{focus}"
        if property_id == "focus":
            return str(values.get("focus", 0))
        return "set"
    return "?"


def _row_for_node(step: PropertyStep, node_path: str) -> list[str]:
    columns = ["", ""]
    assignments = step.assignments.get(node_path)
    for col in range(2, 8):
        prop_id = _PROPERTY_COLUMNS[col]
        if assignments is None:
            columns.append("-")
            continue
        assignment = assignments.by_property.get(prop_id)
        if assignment is None:
            columns.append("-")
        else:
            columns.append(_summary_for(prop_id, assignment))
    return columns


class StepFixtureTree(QTreeWidget):
    """Tree of steps and selected fixtures/segments with per-property summary columns."""

    selection_changed = Signal(int, str, str)

    def __init__(self, model: PropertyCueFilterModel, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self._current_cue_index: int = -1
        self.setColumnCount(len(_COLUMNS))
        self.setHeaderLabels(list(_COLUMNS))
        self.itemClicked.connect(self._on_item_clicked)

    def set_current_cue(self, cue_index: int) -> None:
        self._current_cue_index = cue_index
        self._rebuild()

    def refresh(self) -> None:
        self._rebuild()

    def _current_cue(self) -> PropertyCue | None:
        if self._current_cue_index < 0:
            return None
        if self._current_cue_index >= len(self._model.cues):
            return None
        return self._model.cues[self._current_cue_index]

    def _node_paths(self) -> list[str]:
        paths: list[str] = []
        for entry in self._model.fixture_selection.entries:
            if entry.kind is SelectionEntryKind.FIXTURE:
                paths.append(f"fixture:{entry.id}")
            elif entry.kind is SelectionEntryKind.GROUP:
                paths.append(f"group:{entry.id}")
        return paths

    def _rebuild(self) -> None:
        self.clear()
        cue = self._current_cue()
        if cue is None:
            return
        node_paths = self._node_paths()
        for step_index, step in enumerate(cue.steps):
            step_item = QTreeWidgetItem()
            step_label = step.name or f"Step {step_index + 1}"
            step_item.setText(0, f"{step_label} ({_fmt_time_40hz(step.duration_40hz)})")
            step_item.setText(1, _fmt_time_40hz(step.fade_in_40hz))
            step_item.setData(0, _ROLE_STEP_INDEX, step_index)
            step_item.setData(0, _ROLE_NODE_PATH, "")
            self.addTopLevelItem(step_item)
            for node_path in node_paths:
                node_item = QTreeWidgetItem()
                node_item.setText(0, node_path)
                row = _row_for_node(step, node_path)
                for col, text in enumerate(row):
                    if col >= 2:
                        node_item.setText(col, text)
                node_item.setData(0, _ROLE_STEP_INDEX, step_index)
                node_item.setData(0, _ROLE_NODE_PATH, node_path)
                step_item.addChild(node_item)
            step_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        step_index = item.data(0, _ROLE_STEP_INDEX)
        node_path = item.data(0, _ROLE_NODE_PATH)
        if step_index is None:
            return
        if node_path is None:
            node_path = ""
        if node_path == "":
            self.selection_changed.emit(int(step_index), "", "")
            return
        if column < 2:
            self.selection_changed.emit(int(step_index), str(node_path), "")
            return
        prop_id = _PROPERTY_COLUMNS.get(column, "")
        self.selection_changed.emit(int(step_index), str(node_path), prop_id)
