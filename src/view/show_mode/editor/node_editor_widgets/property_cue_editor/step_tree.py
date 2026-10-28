"""Step / fixture tree with read-only per-property summary columns.

Steps are top-level items showing name + duration + fade-in and a short
summary of each assigned property. Children are the selected fixtures /
groups shown by their display name with the same per-property summary
columns at the fixture/group level.

Clicking anywhere emits ``(step_index, node_path)``. ``node_path`` is ``""``
for a step row so the property pane can offer step-level assignments. The
property columns are purely informational -- editing happens via the tabs
in the property pane.
"""

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
    from collections.abc import Callable

    from PySide6.QtWidgets import QWidget

    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.model.property_cue import PropertyCue
    from model.virtual_filters.property_cues.model.property_step import PropertyStep


_COLUMNS = ("Name", "Fade-in", "Dimmer", "Position", "Gobo", "Colour", "Beam", "Focus")
_PROPERTY_COLUMNS: dict[int, str] = {
    2: "dimmer", 3: "position", 4: "gobo", 5: "colour", 6: "beam", 7: "focus",
}
_ROLE_STEP_INDEX = Qt.ItemDataRole.UserRole + 1
_ROLE_NODE_PATH = Qt.ItemDataRole.UserRole + 2


def _fmt_time_40hz(ticks: int) -> str:
    return f"{ticks / 40.0:.2f}s"


def _summary_for(property_id: str, assignment: object) -> str:
    if isinstance(assignment, PresetPropertyAssignment):
        return assignment.preset_id
    if isinstance(assignment, ManualPropertyAssignment):
        values = assignment.values
        if property_id == "dimmer":
            try:
                return f"{float(values.get('brightness', 0.0)):.2f}"
            except (TypeError, ValueError):
                return "?"
        if property_id == "position":
            try:
                return f"{float(values.get('pan_value', 0.0)):.2f}/{float(values.get('tilt_value', 0.0)):.2f}"
            except (TypeError, ValueError):
                return "?"
        if property_id == "colour":
            colour = values.get("color")
            return str(colour) if colour is not None else "set"
        if property_id == "gobo":
            slots = values.get("slots", {})
            if isinstance(slots, dict) and slots:
                return ",".join(str(v) for v in slots.values())
            return "0"
        if property_id == "beam":
            return f"f{values.get('focus', 0)}"
        if property_id == "focus":
            return str(values.get("focus", 0))
        return "set"
    return "-"


def _summary_cells(step: PropertyStep, node_path: str) -> list[str]:
    assignments = step.assignments.get(node_path)
    cells: list[str] = []
    for col in range(2, 8):
        prop_id = _PROPERTY_COLUMNS[col]
        if assignments is None:
            cells.append("-")
            continue
        cells.append(_summary_for(prop_id, assignments.by_property.get(prop_id)))
    return cells


class StepFixtureTree(QTreeWidget):
    """Tree of steps and selected fixtures/groups with per-property summary columns."""

    selection_changed = Signal(int, str)

    def __init__(
        self,
        model: PropertyCueFilterModel,
        name_resolver: Callable[[str, str], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Build the tree.

        ``name_resolver(kind, id)`` returns the display label for a fixture or
        group. ``kind`` is ``"fixture"`` or ``"group"``. When ``None`` the raw
        id is shown.
        """
        super().__init__(parent)
        self._model = model
        self._name_resolver = name_resolver or (lambda _kind, raw_id: raw_id)
        self._current_cue_index: int = -1
        self.setColumnCount(len(_COLUMNS))
        self.setHeaderLabels(list(_COLUMNS))
        self.itemClicked.connect(self._on_item_clicked)

    def set_name_resolver(self, resolver: Callable[[str, str], str] | None) -> None:
        self._name_resolver = resolver or (lambda _kind, raw_id: raw_id)
        self._rebuild()

    def set_current_cue(self, cue_index: int) -> None:
        self._current_cue_index = cue_index
        self._rebuild()

    def refresh(self) -> None:
        """Rebuild while trying to preserve the previously-selected item."""
        saved = self._captured_selection()
        self._rebuild()
        if saved is not None:
            self._reselect(*saved)

    def _captured_selection(self) -> tuple[int, str] | None:
        current = self.currentItem()
        if current is None:
            return None
        step_index = current.data(0, _ROLE_STEP_INDEX)
        node_path = current.data(0, _ROLE_NODE_PATH)
        if step_index is None:
            return None
        return int(step_index), str(node_path or "")

    def _reselect(self, step_index: int, node_path: str) -> None:
        if step_index < 0 or step_index >= self.topLevelItemCount():
            return
        step_item = self.topLevelItem(step_index)
        if node_path == "":
            self.setCurrentItem(step_item)
            return
        for i in range(step_item.childCount()):
            child = step_item.child(i)
            if child.data(0, _ROLE_NODE_PATH) == node_path:
                self.setCurrentItem(child)
                return
        self.setCurrentItem(step_item)

    def _current_cue(self) -> PropertyCue | None:
        if 0 <= self._current_cue_index < len(self._model.cues):
            return self._model.cues[self._current_cue_index]
        return None

    def _node_paths(self) -> list[tuple[str, str]]:
        """Return (node_path, display_label) tuples for the current fixture selection."""
        rows: list[tuple[str, str]] = []
        for entry in self._model.fixture_selection.entries:
            if entry.kind is SelectionEntryKind.FIXTURE:
                rows.append((f"fixture:{entry.id}", self._name_resolver("fixture", entry.id)))
            elif entry.kind is SelectionEntryKind.GROUP:
                rows.append((f"group:{entry.id}", self._name_resolver("group", entry.id)))
        return rows

    def _apply_summary(self, item: QTreeWidgetItem, cells: list[str]) -> None:
        for col, text in enumerate(cells, start=2):
            item.setText(col, text)

    def _rebuild(self) -> None:
        self.clear()
        cue = self._current_cue()
        if cue is None:
            return
        rows = self._node_paths()
        for step_index, step in enumerate(cue.steps):
            step_item = QTreeWidgetItem()
            step_label = step.name or f"Step {step_index + 1}"
            step_item.setText(0, f"{step_label} ({_fmt_time_40hz(step.duration_40hz)})")
            step_item.setText(1, _fmt_time_40hz(step.fade_in_40hz))
            self._apply_summary(step_item, _summary_cells(step, ""))
            step_item.setData(0, _ROLE_STEP_INDEX, step_index)
            step_item.setData(0, _ROLE_NODE_PATH, "")
            self.addTopLevelItem(step_item)
            for node_path, label in rows:
                node_item = QTreeWidgetItem()
                node_item.setText(0, label)
                self._apply_summary(node_item, _summary_cells(step, node_path))
                node_item.setData(0, _ROLE_STEP_INDEX, step_index)
                node_item.setData(0, _ROLE_NODE_PATH, node_path)
                step_item.addChild(node_item)
            step_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        step_index = item.data(0, _ROLE_STEP_INDEX)
        node_path = item.data(0, _ROLE_NODE_PATH)
        if step_index is None:
            return
        self.selection_changed.emit(int(step_index), str(node_path or ""))
