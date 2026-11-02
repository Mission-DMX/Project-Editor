"""Fixture selection and enabled-capability state for the property-cue model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger

logger = getLogger(__name__)


class SelectionEntryKind(Enum):
    FIXTURE = "fixture"
    GROUP = "group"


class EnabledCapability(Enum):
    DIMMER = "dimmer"
    POSITION = "position"
    COLOUR = "colour"
    GOBO = "gobo"
    BEAM = "beam"
    FOCUS = "focus"
    FROST = "frost"


@dataclass(slots=True, frozen=True)
class FixtureSelectionEntry:
    kind: SelectionEntryKind
    id: str


@dataclass(slots=True)
class FixtureSelection:
    entries: list[FixtureSelectionEntry] = field(default_factory=list)
    enabled_capabilities: set[EnabledCapability] = field(default_factory=set)

    def to_json(self) -> dict:
        return {
            "entries": [
                {"kind": entry.kind.value, "id": entry.id}
                for entry in self.entries
            ],
            "enabled_capabilities": [cap.value for cap in self.enabled_capabilities],
        }

    @classmethod
    def from_json(cls, blob: dict) -> FixtureSelection:
        entries_blob = blob.get("entries", [])
        entries: list[FixtureSelectionEntry] = []
        for entry_blob in entries_blob:
            kind = SelectionEntryKind(entry_blob["kind"])
            entries.append(FixtureSelectionEntry(kind=kind, id=entry_blob["id"]))
        capabilities_blob = blob.get("enabled_capabilities", [])
        capabilities = {EnabledCapability(cap) for cap in capabilities_blob}
        return cls(entries=entries, enabled_capabilities=capabilities)

    def diff(
        self, other: FixtureSelection,
    ) -> tuple[list[FixtureSelectionEntry], list[FixtureSelectionEntry]]:
        """Return (added_entries, removed_entries) comparing ``self`` → ``other``.

        ``added`` are entries present in ``other`` but not in ``self``.
        ``removed`` are entries present in ``self`` but not in ``other``.
        """
        self_set = set(self.entries)
        other_set = set(other.entries)
        added = [entry for entry in other.entries if entry not in self_set]
        removed = [entry for entry in self.entries if entry not in other_set]
        return added, removed
