"""Right-hand editor pane: step timings (when a step is selected) + property tabs.

Property tabs are the full set of per-property editors. Tabs whose capability
isn't in :class:`FixtureSelection.enabled_capabilities` are disabled. Clicking a
step row loads step timings in the top panel and keeps the tab widget visible
so step-level overrides can still be dialed in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QStackedWidget, QTabWidget, QVBoxLayout, QWidget

from model.ofl.capability_discovery import discover_capabilities
from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability

from .editors.beam_editor import BeamEditor
from .editors.colour_editor import ColourEditor
from .editors.dimmer_editor import DimmerEditor
from .editors.focus_editor import FocusEditor
from .editors.frost_editor import FrostEditor
from .editors.gobo_editor import GoboEditor
from .editors.position_editor import PositionEditor
from .editors.step_editor import StepEditor

if TYPE_CHECKING:
    from collections.abc import Callable

    from model.ofl.fixture import UsedFixture
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


_PROPERTY_ORDER: tuple[tuple[str, str, EnabledCapability], ...] = (
    ("dimmer", "Dimmer", EnabledCapability.DIMMER),
    ("position", "Position", EnabledCapability.POSITION),
    ("colour", "Colour", EnabledCapability.COLOUR),
    ("gobo", "Gobo", EnabledCapability.GOBO),
    ("beam", "Beam", EnabledCapability.BEAM),
    ("focus", "Focus", EnabledCapability.FOCUS),
    ("frost", "Frost", EnabledCapability.FROST),
)


class PropertyPane(QWidget):
    """Shows the step editor (when a step is selected) above a tab widget of per-property editors."""

    assignment_applied = Signal()

    def __init__(
        self,
        model: PropertyCueFilterModel,
        fixture_lookup: Callable[[str], list[UsedFixture]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._fixture_lookup = fixture_lookup or (lambda _np: [])
        self._cue_index: int = -1
        self._step_index: int = -1
        self._node_path: str = ""

        root = QVBoxLayout()
        self.setLayout(root)

        self._placeholder = QLabel("Add a cue, then select a step or fixture to edit.")
        self._placeholder.setWordWrap(True)
        root.addWidget(self._placeholder)

        self._top_stack = QStackedWidget()
        root.addWidget(self._top_stack)
        self._top_blank = QWidget()
        self._top_stack.addWidget(self._top_blank)
        self._step_editor = StepEditor(model)
        self._top_stack.addWidget(self._step_editor)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs, 1)
        self._editors: dict[str, QWidget] = {}
        self._tab_indices: dict[str, int] = {}
        for prop_id, label, _cap in _PROPERTY_ORDER:
            editor = _build_editor(prop_id, model)
            self._editors[prop_id] = editor
            self._tab_indices[prop_id] = self._tabs.addTab(editor, label)
            editor.applied.connect(self.assignment_applied.emit)

        self._step_editor.applied.connect(self.assignment_applied.emit)

        self._placeholder.setVisible(True)
        self._top_stack.setVisible(False)
        self._tabs.setVisible(False)
        self._apply_capability_filter()

    def set_current_cue(self, cue_index: int) -> None:
        self._cue_index = cue_index

    def recommended_minimum_height(self) -> int:
        """Return the height needed to display the pane without clipping.

        When a step row is selected both the step editor (name/duration/fade-in)
        and the tab widget are visible side-by-side vertically; this method sums
        the natural height of both so the pane fits the worst case. For every
        tab we read ``QWidget.sizeHint().height()`` so there are no magic
        numbers. The tab bar overhead is already covered by
        ``QTabWidget.sizeHint`` -- we take the max of the tabs' hint and the
        editors' individual hints to be defensive against stylesheet
        differences. Returns 0 when the pane carries no editors yet.
        """
        tab_hint = self._tabs.sizeHint().height()
        editor_hint = max(
            (editor.sizeHint().height() for editor in self._editors.values()),
            default=0,
        )
        step_hint = self._step_editor.sizeHint().height()
        return max(tab_hint, editor_hint) + step_hint

    def refresh_capabilities(self) -> None:
        """Re-evaluate which tabs are enabled from the current fixture selection."""
        self._apply_capability_filter()

    def show_editor(self, step_index: int, node_path: str) -> None:
        self._step_index = step_index
        self._node_path = node_path
        if self._cue_index < 0 or step_index < 0:
            self._placeholder.setVisible(True)
            self._top_stack.setVisible(False)
            self._tabs.setVisible(False)
            return
        self._placeholder.setVisible(False)
        if node_path == "":
            self._top_stack.setCurrentWidget(self._step_editor)
            self._step_editor.load(self._cue_index, step_index)
            self._top_stack.setVisible(True)
        else:
            self._top_stack.setCurrentWidget(self._top_blank)
            self._top_stack.setVisible(False)
        fixtures = self._fixture_lookup(node_path)
        self._editors["gobo"].set_fixtures(fixtures)
        self._apply_capability_filter(fixtures)
        for prop_id, editor in self._editors.items():
            editor.load(self._cue_index, step_index, node_path)
            # Reflect loaded state in the tab label (prefix * if an assignment exists).
            index = self._tab_indices[prop_id]
            has_assignment = editor._current_assignment() is not None
            label = self._tabs.tabText(index).lstrip("* ")
            self._tabs.setTabText(index, f"* {label}" if has_assignment else label)
        self._tabs.setVisible(True)

    def _apply_capability_filter(self, fixtures: list[UsedFixture] | None = None) -> None:
        """Gate tabs by the selection's enabled capabilities AND per-fixture availability.

        When ``fixtures`` is empty we only check the global enabled set so tabs
        remain visible after fixture configuration but before a specific node is
        clicked.
        """
        enabled = set(self._model.fixture_selection.enabled_capabilities)
        # ``discover_capabilities`` returns capability tags (strings) so the
        # OFL helper does not depend on the vfilter's EnabledCapability enum.
        per_selection = discover_capabilities(fixtures) if fixtures else None
        for prop_id, _label, cap in _PROPERTY_ORDER:
            allowed = cap in enabled
            if allowed and per_selection is not None:
                allowed = cap.value in per_selection
            self._tabs.setTabEnabled(self._tab_indices[prop_id], allowed)


def _build_editor(prop_id: str, model: PropertyCueFilterModel) -> QWidget:
    if prop_id == "dimmer":
        return DimmerEditor(model)
    if prop_id == "position":
        return PositionEditor(model)
    if prop_id == "colour":
        return ColourEditor(model)
    if prop_id == "gobo":
        return GoboEditor(model)
    if prop_id == "beam":
        return BeamEditor(model)
    if prop_id == "focus":
        return FocusEditor(model)
    if prop_id == "frost":
        return FrostEditor(model)
    raise ValueError(f"Unknown property id: {prop_id!r}")
