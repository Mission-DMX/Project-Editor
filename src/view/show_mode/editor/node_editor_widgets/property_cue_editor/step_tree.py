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

from model.virtual_filters.property_cues._property_registry import properties_in_order
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


# S1: the step tree's property columns derive from the registry so a new
# property class only needs to add a :class:`PropertyEntry` with a
# ``step_tree_column`` for the column to appear here.
_PROPERTY_COLUMN_SEQUENCE: tuple[tuple[str, str], ...] = tuple(
    (e.id, e.step_tree_column)
    for e in properties_in_order()
    if e.step_tree_column is not None
)
_COLUMNS: tuple[str, ...] = ("Name", "Fade-in", *(label for _pid, label in _PROPERTY_COLUMN_SEQUENCE))
# Column index -> property id. Static columns ("Name", "Fade-in") occupy 0..1.
_PROPERTY_COLUMNS: dict[int, str] = {
    i + 2: pid for i, (pid, _label) in enumerate(_PROPERTY_COLUMN_SEQUENCE)
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
        if property_id == "color":
            colors = values.get("colors") or {}
            if isinstance(colors, dict) and colors:
                first_key = next(iter(sorted(colors.keys())))
                return f"{colors[first_key]}" if len(colors) == 1 else f"{len(colors)} colors"
            return "-"
        if property_id == "gobo":
            slots = values.get("slots", {})
            if isinstance(slots, dict) and slots:
                return ",".join(str(v) for v in slots.values())
            return "0"
        if property_id == "beam":
            # L22: focus has moved to its own property; show the beam sub-channels
            # the current BeamProperty actually exposes instead of the stale
            # ``focus`` summary.
            parts = [f"{key[0]}{values[key]}"
                     for key in ("zoom", "iris", "prism_selection")
                     if key in values]
            return "/".join(parts) if parts else "set"
        if property_id == "focus":
            return str(values.get("focus", 0))
        if property_id == "frost":
            return str(values.get("frost_intensity", 0))
        return "set"
    return "-"


def _summary_cells(step: PropertyStep, node_path: str) -> list[str]:
    assignments = step.assignments.get(node_path)
    cells: list[str] = []
    for col in sorted(_PROPERTY_COLUMNS):
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
        # L24: keyboard arrows must update the property pane too. Clicking
        # fires both ``itemClicked`` and ``currentItemChanged`` but keyboard
        # navigation only fires the latter, so listen on both. The click
        # handler forwards to the same slot as the selection change.
        self.itemClicked.connect(self._on_item_clicked)
        self.currentItemChanged.connect(self._on_current_item_changed)

    def set_name_resolver(self, resolver: Callable[[str, str], str] | None) -> None:
        """Install a resolver that maps (kind, raw id) pairs to display names."""
        self._name_resolver = resolver or (lambda _kind, raw_id: raw_id)
        self._rebuild()

    def set_current_cue(self, cue_index: int) -> None:
        """Switch the tree to show steps of the given cue index."""
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
        self._emit_selection_for(item)

    def _on_current_item_changed(
        self, item: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None,
    ) -> None:
        if item is None:
            return
        self._emit_selection_for(item)

    def _emit_selection_for(self, item: QTreeWidgetItem) -> None:
        step_index = item.data(0, _ROLE_STEP_INDEX)
        node_path = item.data(0, _ROLE_NODE_PATH)
        if step_index is None:
            return
        self.selection_changed.emit(int(step_index), str(node_path or ""))

    def current_step_index(self) -> int:
        """Return the step index of the current selection, or -1 if nothing is selected."""
        saved = self._captured_selection()
        if saved is None:
            return -1
        return saved[0]

    def select_step(self, cue_index: int, step_index: int) -> None:
        """Programmatically move the selection to ``(cue_index, step_index)``.

        Switches the tree to ``cue_index`` first if the current cue differs.
        Used by the XTouch forward/rev handlers to drive the preview from
        the hardware transport controls.
        """
        if cue_index != self._current_cue_index:
            self.set_current_cue(cue_index)
        self._reselect(step_index, "")
