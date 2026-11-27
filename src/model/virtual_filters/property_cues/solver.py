"""Keyframe solver (WP3).

Consumes :class:`RequestGroup` objects emitted by property and preset invocations
and produces a per-channel stream of :class:`KeyFrame` instances suitable for a
native cue filter.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING

from model.virtual_filters.property_cues.solver_helpers import (
    make_frame,
    slot_from_seconds,
)

if TYPE_CHECKING:
    from model.filter_data.cues.cue import KeyFrame
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec
    from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest


logger = getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RequestGroup:
    """A set of keyframe requests emitted together by a single property/preset invocation.

    Groups with FEWER member channels are considered MORE specialised and win over groups
    with more channels on contested channels. On a tie, higher ``tree_depth`` (deeper in
    the step/fixture tree) wins.
    """

    origin_label: str
    tree_depth: int
    channel_names: frozenset[str]
    requests: dict[str, list[KeyframeRequest]]


@dataclass(slots=True)
class SolveInput:
    """Everything the solver needs for a single cue."""

    channel_specs: dict[str, ChannelSpec]
    groups: list[RequestGroup]


@dataclass(slots=True)
class SolvedChannel:
    """Resulting keyframe stream for one output channel."""

    name: str
    frames: list[KeyFrame]


class KeyframeSolver:
    """Resolves overlapping ``RequestGroup`` streams into per-channel keyframes."""

    def solve(self, inp: SolveInput) -> dict[str, SolvedChannel]:
        """See module docstring for the algorithm."""
        winners = _select_winners(inp.groups)
        result: dict[str, SolvedChannel] = {}
        for channel_name, surviving in winners.items():
            spec = inp.channel_specs.get(channel_name)
            if spec is None:
                continue
            request_stream = _dedupe_and_sort(surviving)
            if not request_stream:
                continue
            # L4: cross-group interpolation is now handled in the native
            # builder's ``_state_for``. The solver just emits one frame per
            # surviving request; the builder fills intermediate slots when
            # another channel contributes a slot this one does not have.
            frames = _materialise(spec, request_stream)
            result[channel_name] = SolvedChannel(name=channel_name, frames=frames)
        return result


def _select_winners(
    groups: list[RequestGroup],
) -> dict[str, list[tuple[KeyframeRequest, RequestGroup]]]:
    """Deduplicate per-channel/per-slot requests.

    Returns a mapping ``channel -> [(request, originating_group), ...]`` with
    at most one survivor per slot, preserving the group each request originated
    from. Precedence between step- and fixture-level assignments is resolved
    upstream in :func:`_collect_cue` (L6), so here we simply keep the latest
    emission at any contested slot — later group index wins on a tie, matching
    "last-write-wins" semantics within a cue.
    """
    best: dict[str, dict[int, tuple[int, KeyframeRequest, RequestGroup]]] = {}
    for group_index, group in enumerate(groups):
        for channel_name, requests in group.requests.items():
            if channel_name not in group.channel_names:
                continue
            per_slot = best.setdefault(channel_name, {})
            for req in requests:
                slot = int(req.timestep_40hz)
                existing = per_slot.get(slot)
                if existing is None or group_index >= existing[0]:
                    per_slot[slot] = (group_index, req, group)
    out: dict[str, list[tuple[KeyframeRequest, RequestGroup]]] = {}
    for channel_name, per_slot in best.items():
        ordered = sorted(per_slot.items(), key=lambda kv: kv[0])
        out[channel_name] = [(entry[1], entry[2]) for _, entry in ordered]
    return out


def _dedupe_and_sort(
    stream: list[tuple[KeyframeRequest, RequestGroup]],
) -> list[tuple[KeyframeRequest, RequestGroup]]:
    """Return the stream sorted by slot (already de-duplicated per slot in winner step)."""
    return sorted(stream, key=lambda rg: int(rg[0].timestep_40hz))


def _materialise(
    spec: ChannelSpec,
    request_stream: list[tuple[KeyframeRequest, RequestGroup]],
) -> list[KeyFrame]:
    """Build :class:`KeyFrame` instances from the surviving requests, one per request.

    Cross-channel interpolation at slots this channel does not touch is
    handled in :func:`_native_builder._state_for` using the next frame's
    transition (F1). The solver no longer inserts synthetic mid-frames.
    """
    frames: list[KeyFrame] = []
    for req, _group in request_stream:
        slot = int(req.timestep_40hz)
        frames.append(make_frame(spec, slot, req.transition, req.requested_value))
    return _collapse_same_slot(frames)


def _collapse_same_slot(frames: list[KeyFrame]) -> list[KeyFrame]:
    """Keep only the last frame per 40 Hz slot, preserving insertion order within a slot."""
    by_slot: dict[int, KeyFrame] = {}
    for kf in frames:
        by_slot[slot_from_seconds(kf.timestamp)] = kf
    ordered_slots = sorted(by_slot.keys())
    return [by_slot[s] for s in ordered_slots]
