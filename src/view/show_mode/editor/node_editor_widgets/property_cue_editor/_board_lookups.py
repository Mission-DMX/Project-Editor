"""Board-driven lookups used by the property-cue editor shell + wizard.

Centralises the tiny attribute walkers that iterate a
``BoardConfiguration`` so the editor widget, the fixture-selection
wizard, and any future consumer agree on how to tolerate detached
stages / missing attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model.ofl.fixture import UsedFixture
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


def iter_fixtures(board: object | None) -> list:
    """Return ``board.fixtures`` as a list, tolerant of missing / None attrs."""
    if board is None:
        return []
    return list(getattr(board, "fixtures", []) or [])


def iter_groups(board: object | None) -> list:
    """Return the stage's groups as a list, tolerant of detached stages."""
    if board is None:
        return []
    stage = getattr(board, "stage_config", None)
    if stage is None:
        return []
    return list(getattr(stage, "groups", []) or [])


def _fixture_in_any_group(fixture: object, group_ids: set[str], board: object) -> bool:
    fid = str(getattr(fixture, "uuid", ""))
    for group in iter_groups(board):
        if getattr(group, "id", None) in group_ids and fid in (getattr(group, "member_ids", []) or []):
            return True
    return False


def resolve_node_name(board: object | None, kind: str, raw_id: str) -> str:
    if board is None:
        return raw_id
    if kind == "fixture":
        for fixture in iter_fixtures(board):
            if str(getattr(fixture, "uuid", "")) == raw_id:
                return getattr(fixture, "name_on_stage", None) or getattr(fixture, "name", None) or raw_id
    elif kind == "group":
        for group in iter_groups(board):
            if getattr(group, "id", None) == raw_id:
                return getattr(group, "name", None) or raw_id
    return raw_id


def lookup_fixtures(
    board: object | None,
    model: PropertyCueFilterModel | None,
    node_path: str,
) -> list[UsedFixture]:
    """Resolve ``node_path`` to the ``UsedFixture`` objects it represents.

    - ``""`` → every fixture reachable from the selection (direct + via groups).
    - ``"fixture:UUID"`` → the matching single fixture (if present on the board).
    - ``"group:ID"`` → every fixture whose UUID is in that group's member list.
    """
    if board is None or model is None:
        return []
    fixtures = iter_fixtures(board)
    if not node_path:
        selection = model.fixture_selection
        fixture_ids = {e.id for e in selection.entries if e.kind.value == "fixture"}
        group_ids = {e.id for e in selection.entries if e.kind.value == "group"}
        return [
            f for f in fixtures
            if str(getattr(f, "uuid", "")) in fixture_ids
            or _fixture_in_any_group(f, group_ids, board)
        ]
    if node_path.startswith("fixture:"):
        fid = node_path[len("fixture:"):]
        return [f for f in fixtures if str(getattr(f, "uuid", "")) == fid]
    if node_path.startswith("group:"):
        gid = node_path[len("group:"):]
        return [f for f in fixtures if _fixture_in_any_group(f, {gid}, board)]
    return []


def resolve_fixtures_from_entries(board: object | None, selection: Iterable) -> list[UsedFixture]:
    """Expand a ``FixtureSelection`` into the ``UsedFixture`` objects it covers.

    Fixtures reached via selected groups are included. ``selection`` can be
    either an iterable of :class:`FixtureSelectionEntry` or an object with an
    ``entries`` attribute (e.g. :class:`FixtureSelection`).
    """
    if board is None:
        return []
    entries = getattr(selection, "entries", selection)
    fixture_ids: set[str] = set()
    group_ids: set[str] = set()
    for entry in entries:
        kind = entry.kind.value if hasattr(entry.kind, "value") else str(entry.kind)
        if kind == "fixture":
            fixture_ids.add(entry.id)
        elif kind == "group":
            group_ids.add(entry.id)
    if group_ids:
        for group in iter_groups(board):
            if getattr(group, "id", None) in group_ids:
                fixture_ids.update(getattr(group, "member_ids", []) or [])
    return [f for f in iter_fixtures(board) if str(getattr(f, "uuid", "")) in fixture_ids]
