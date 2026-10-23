"""QWizard for selecting fixtures/groups and the capabilities they contribute.

The wizard has two pages:
    1. ``_FixturePickerPage`` presents a check-tree of all fixtures and
       fixture groups available on the board/stage.
    2. ``_CapabilityPickerPage`` lists every ``EnabledCapability`` whose
       underlying ``CapabilityType`` is present in at least one selected
       fixture, each with a checkbox.

The result is retrievable via :meth:`FixtureSelectionWizard.result_selection`
and is ``None`` when the user cancels.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from model.virtual_filters.property_cues.model.fixture_selection import (
    EnabledCapability,
    FixtureSelection,
    FixtureSelectionEntry,
    SelectionEntryKind,
)

from ._capability_discovery import discover_capabilities

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from model.board_configuration import BoardConfiguration
    from model.ofl.fixture import UsedFixture

logger = getLogger(__name__)

_ROLE_ENTRY = Qt.ItemDataRole.UserRole + 1
_ROLE_CAPABILITY = Qt.ItemDataRole.UserRole + 2


def _fixture_label(fixture: UsedFixture) -> str:
    """Return a human-readable label for a fixture (uses stage name if set)."""
    name = (
        getattr(fixture, "name_on_stage", None)
        or getattr(fixture, "name", None)
        or getattr(fixture, "short_name", None)
        or "?"
    )
    universe = getattr(fixture, "universe_id", "?")
    start = getattr(fixture, "start_index", "?")
    return f"{name} (U{universe}/CH{start})"


def _fixture_id(fixture: UsedFixture) -> str:
    """Stable string id for a UsedFixture (its UUID)."""
    return str(getattr(fixture, "uuid", ""))


def _collect_groups(board: BoardConfiguration) -> list:
    """Collect fixture groups from the board. Groups live on the stage config,
    which is not always wired up to BoardConfiguration; fall back to an empty
    list rather than erroring if the attribute isn't present."""
    stage = getattr(board, "stage_config", None)
    if stage is None:
        return []
    return list(getattr(stage, "groups", []) or [])


class _FixturePickerPage(QWizardPage):
    """Page 1: pick fixtures and/or fixture groups via a check-tree."""

    def __init__(self, board: BoardConfiguration, initial: FixtureSelection | None) -> None:
        super().__init__()
        self.setTitle("Select Fixtures")
        self.setSubTitle(
            "Choose the fixtures and fixture groups that should contribute "
            "properties to this cue filter."
        )
        self._board = board

        layout = QVBoxLayout(self)
        self._tree = QTreeWidget(self)
        self._tree.setColumnCount(1)
        self._tree.setHeaderLabels(["Fixtures and Groups"])
        layout.addWidget(self._tree)

        initial_ids = (
            {entry.id for entry in initial.entries} if initial is not None else set()
        )

        self._fixture_root = QTreeWidgetItem(self._tree, ["Fixtures"])
        self._fixture_root.setFlags(self._fixture_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self._fixture_root.setExpanded(True)
        for fixture in getattr(board, "fixtures", []) or []:
            fid = _fixture_id(fixture)
            item = QTreeWidgetItem(self._fixture_root, [_fixture_label(fixture)])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                0,
                Qt.CheckState.Checked if fid in initial_ids else Qt.CheckState.Unchecked,
            )
            item.setData(
                0,
                _ROLE_ENTRY,
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=fid),
            )

        self._group_root = QTreeWidgetItem(self._tree, ["Groups"])
        self._group_root.setFlags(self._group_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self._group_root.setExpanded(True)
        for group in _collect_groups(board):
            gid = getattr(group, "id", None)
            if gid is None:
                continue
            label = getattr(group, "name", "") or gid
            item = QTreeWidgetItem(self._group_root, [label])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                0,
                Qt.CheckState.Checked if gid in initial_ids else Qt.CheckState.Unchecked,
            )
            item.setData(
                0,
                _ROLE_ENTRY,
                FixtureSelectionEntry(kind=SelectionEntryKind.GROUP, id=gid),
            )

    def selected_entries(self) -> list[FixtureSelectionEntry]:
        """Return the currently-checked fixture/group entries, in display order."""
        entries: list[FixtureSelectionEntry] = []
        for root in (self._fixture_root, self._group_root):
            for i in range(root.childCount()):
                child = root.child(i)
                if child.checkState(0) != Qt.CheckState.Checked:
                    continue
                entry = child.data(0, _ROLE_ENTRY)
                if isinstance(entry, FixtureSelectionEntry):
                    entries.append(entry)
        return entries

    def selected_fixtures(self) -> list[UsedFixture]:
        """Return the UsedFixture objects for the current fixture selection,
        including fixtures reached transitively through selected groups."""
        selected_entries = self.selected_entries()
        fixture_ids = {e.id for e in selected_entries if e.kind == SelectionEntryKind.FIXTURE}
        group_ids = {e.id for e in selected_entries if e.kind == SelectionEntryKind.GROUP}

        if group_ids:
            for group in _collect_groups(self._board):
                if getattr(group, "id", None) in group_ids:
                    fixture_ids.update(getattr(group, "member_ids", []) or [])

        fixtures: list[UsedFixture] = [
            fixture
            for fixture in getattr(self._board, "fixtures", []) or []
            if _fixture_id(fixture) in fixture_ids
        ]
        return fixtures


class _CapabilityPickerPage(QWizardPage):
    """Page 2: tick which EnabledCapabilities contribute to this cue filter."""

    def __init__(self, picker_page: _FixturePickerPage, initial: FixtureSelection | None) -> None:
        super().__init__()
        self.setTitle("Enable Capabilities")
        self.setSubTitle(
            "Pick the properties you want to control. Only capabilities present "
            "in at least one selected fixture are shown."
        )
        self._picker_page = picker_page
        self._initial = initial.enabled_capabilities if initial is not None else set()

        layout = QVBoxLayout(self)
        self._hint = QLabel("Select at least one capability.")
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)
        self._list = QListWidget(self)
        layout.addWidget(self._list)

    def initializePage(self) -> None:  # noqa: N802 — Qt override
        """Rebuild the capability list from the fixture selection on first show."""
        self._list.clear()
        fixtures = self._picker_page.selected_fixtures()
        available = discover_capabilities(fixtures)
        if not available:
            self._hint.setText(
                "No capabilities could be derived from the selected fixtures. "
                "Pick a different set of fixtures or add capabilities manually later."
            )
            return
        self._hint.setText("Tick the capabilities you want to control.")
        # Preserve EnabledCapability declaration order for stable UI.
        for cap in EnabledCapability:
            if cap not in available:
                continue
            item = QListWidgetItem(cap.value.capitalize(), self._list)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if cap in self._initial else Qt.CheckState.Unchecked,
            )
            item.setData(_ROLE_CAPABILITY, cap)

    def enabled_capabilities(self) -> set[EnabledCapability]:
        """Return the currently-checked capabilities."""
        result: set[EnabledCapability] = set()
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            cap = item.data(_ROLE_CAPABILITY)
            if isinstance(cap, EnabledCapability):
                result.add(cap)
        return result


class FixtureSelectionWizard(QWizard):
    """Two-page wizard to compose a :class:`FixtureSelection`."""

    def __init__(
        self,
        board: BoardConfiguration,
        initial: FixtureSelection | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configure Fixtures")
        self.setMinimumSize(520, 420)
        self._initial = initial
        self._result: FixtureSelection | None = None
        self._msgbox: QMessageBox | None = None

        self._picker_page = _FixturePickerPage(board, initial)
        self._capability_page = _CapabilityPickerPage(self._picker_page, initial)
        self.addPage(self._picker_page)
        self.addPage(self._capability_page)

    def result_selection(self) -> FixtureSelection | None:
        """Return the chosen selection, or ``None`` if the user cancelled."""
        return self._result

    def _compose_selection(self) -> FixtureSelection:
        return FixtureSelection(
            entries=self._picker_page.selected_entries(),
            enabled_capabilities=self._capability_page.enabled_capabilities(),
        )

    def _removed_entries(self, candidate: FixtureSelection) -> list[FixtureSelectionEntry]:
        """Return the entries present in ``initial`` but missing from ``candidate``."""
        if self._initial is None:
            return []
        _, removed = self._initial.diff(candidate)
        return removed

    def accept(self) -> None:
        """Confirm the wizard, warning the user if the change loses prior data."""
        candidate = self._compose_selection()
        removed = self._removed_entries(candidate)
        if removed:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Confirm fixture removal")
            removed_desc = ", ".join(f"{e.kind.value}:{e.id}" for e in removed)
            msg.setText(
                "The following previously-selected entries will be removed: "
                f"{removed_desc}.\n\n"
                "Per-fixture settings (preset bindings, offsets and other data) "
                "for the removed items will be lost.\n\n"
                "Do you want to continue?"
            )
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
            )
            msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            # Store on self so the non-blocking dialog isn't GC'd before the user responds.
            self._msgbox = msg
            msg.show()

            def _on_finished(_code: int) -> None:
                clicked = msg.standardButton(msg.clickedButton())
                self._msgbox = None
                if clicked == QMessageBox.StandardButton.Yes:
                    self._result = candidate
                    super(FixtureSelectionWizard, self).accept()

            msg.finished.connect(_on_finished)
            return

        self._result = candidate
        super().accept()
