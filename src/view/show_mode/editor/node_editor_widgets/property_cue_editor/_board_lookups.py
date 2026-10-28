"""Board-driven lookups used by the property-cue editor shell.

Centralises the two helpers that walk a ``BoardConfiguration`` from
the editor widget: resolving a tree node path to its display name and
resolving it to the actual list of ``UsedFixture`` objects it covers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.ofl.fixture import UsedFixture
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


def _fixture_in_any_group(fixture: object, group_ids: set[str], board: object) -> bool:
    stage = getattr(board, "stage_config", None)
    fid = str(getattr(fixture, "uuid", ""))
    for group in (getattr(stage, "groups", []) if stage is not None else []) or []:
        if getattr(group, "id", None) in group_ids and fid in (getattr(group, "member_ids", []) or []):
            return True
    return False


def resolve_node_name(board: object | None, kind: str, raw_id: str) -> str:
    if board is None:
        return raw_id
    if kind == "fixture":
        for fixture in getattr(board, "fixtures", []) or []:
            if str(getattr(fixture, "uuid", "")) == raw_id:
                return getattr(fixture, "name_on_stage", None) or getattr(fixture, "name", None) or raw_id
    elif kind == "group":
        stage = getattr(board, "stage_config", None)
        for group in (getattr(stage, "groups", []) if stage is not None else []) or []:
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
    fixtures = list(getattr(board, "fixtures", []) or [])
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
