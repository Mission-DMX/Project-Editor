"""Top-level ``PropertyCueFilterModel`` stored in ``filter_configurations['cues-prop-data']``."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger

from model.virtual_filters.property_cues.model.fixture_selection import FixtureSelection
from model.virtual_filters.property_cues.model.property_cue import PropertyCue
from model.virtual_filters.property_cues.model.property_step import PropertyAssignments

logger = getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1


class EndAction(Enum):
    HOLD = "hold"
    START_AGAIN = "start_again"
    NEXT_CUE = "next_cue"


@dataclass(slots=True)
class PropertyCueGeneralSettings:
    persistence: bool = False
    default_cue_index: int = -1

    def to_json(self) -> dict:
        return {
            "persistence": self.persistence,
            "default_cue_index": self.default_cue_index,
        }

    @classmethod
    def from_json(cls, blob: dict) -> PropertyCueGeneralSettings:
        return cls(
            persistence=bool(blob.get("persistence", False)),
            default_cue_index=int(blob.get("default_cue_index", -1)),
        )


def _fixture_id_from_path(node_path: str) -> str | None:
    """Return the ``fixture:<id>`` id from a path, or None if not present."""
    for component in node_path.split("/"):
        if component.startswith("fixture:"):
            return component[len("fixture:"):]
    return None


def _closest_shared_ancestor_distance(
    new_memberships: list[str],
    other_memberships: list[str],
) -> int:
    """Return the shared-ancestor depth; higher value = closer common group.

    Group membership lists are ordered closest-first. The depth is the index of
    the first common group counted from the closest; a lower index means
    closer. We return ``len(new_memberships) - closest_index`` so the caller
    can pick the maximum. Returns -1 when there is no shared ancestor.
    """
    other_set = set(other_memberships)
    for idx, group_id in enumerate(new_memberships):
        if group_id in other_set:
            return len(new_memberships) - idx
    return -1


@dataclass(slots=True)
class PropertyCueFilterModel:
    fixture_selection: FixtureSelection = field(default_factory=FixtureSelection)
    general: PropertyCueGeneralSettings = field(default_factory=PropertyCueGeneralSettings)
    cues: list[PropertyCue] = field(default_factory=list)

    def to_json_str(self) -> str:
        blob = {
            "version": CURRENT_SCHEMA_VERSION,
            "fixture_selection": self.fixture_selection.to_json(),
            "general": self.general.to_json(),
            "cues": [cue.to_json() for cue in self.cues],
        }
        return json.dumps(blob)

    def load_from_json_str(self, blob_str: str) -> None:
        """Replace this model's contents from ``blob_str``, keeping the object identity.

        UI widgets cache a reference to this model at construction time; using
        in-place mutation here avoids the "stale model" trap that follows a
        plain reassignment (editors would silently read the pre-reload model
        after a configuration load).
        """
        if blob_str == "":
            self.fixture_selection = FixtureSelection()
            self.general = PropertyCueGeneralSettings()
            self.cues.clear()
            return
        blob = json.loads(blob_str)
        version = blob.get("version")
        if version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported PropertyCueFilterModel schema version: {version!r} "
                f"(expected {CURRENT_SCHEMA_VERSION})",
            )
        self.fixture_selection = FixtureSelection.from_json(blob.get("fixture_selection", {}))
        self.general = PropertyCueGeneralSettings.from_json(blob.get("general", {}))
        self.cues[:] = [PropertyCue.from_json(cue_blob) for cue_blob in blob.get("cues", [])]

    @classmethod
    def from_json_str(cls, blob_str: str) -> PropertyCueFilterModel:
        instance = cls()
        instance.load_from_json_str(blob_str)
        return instance

    def copy_fixture_from_neighbour(
        self,
        new_fixture_path: str,
        fixture_group_memberships: dict[str, list[str]],
    ) -> None:
        """Copy per-property assignments from the closest existing sibling onto the new fixture."""
        new_fixture_id = _fixture_id_from_path(new_fixture_path)
        new_memberships = fixture_group_memberships.get(new_fixture_id or "", [])
        for cue in self.cues:
            for step in cue.steps:
                if new_fixture_path in step.assignments:
                    continue
                if not step.assignments:
                    continue
                best_path: str | None = None
                best_score: int = -1
                for existing_path in step.assignments:
                    existing_fixture_id = _fixture_id_from_path(existing_path)
                    if existing_fixture_id is None:
                        continue
                    existing_memberships = fixture_group_memberships.get(existing_fixture_id, [])
                    score = _closest_shared_ancestor_distance(new_memberships, existing_memberships)
                    if score > best_score:
                        best_score = score
                        best_path = existing_path
                if best_path is None:
                    best_path = next(iter(step.assignments))
                source = step.assignments[best_path]
                step.assignments[new_fixture_path] = PropertyAssignments(
                    by_property=copy.deepcopy(source.by_property),
                )

    def compile_to_native_cue_filter(self) -> None:
        """To be wired in WP9."""
        raise NotImplementedError
