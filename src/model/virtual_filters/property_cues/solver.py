"""Keyframe solver (WP3).

Consumes :class:`RequestGroup` objects emitted by property and preset invocations
and produces a per-channel stream of :class:`KeyFrame` instances suitable for a
native cue filter.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING

from model.filter_data.cues import curves
from model.filter_data.cues.cue import KeyFrame
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.solver_helpers import (
    group_rank,
    make_frame,
    make_state,
    slot_from_seconds,
)

if TYPE_CHECKING:
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
            insertion_slots = _collect_insertion_slots(channel_name, request_stream, winners)
            frames = _materialise(spec, request_stream, insertion_slots)
            result[channel_name] = SolvedChannel(name=channel_name, frames=frames)
        return result


def _select_winners(
    groups: list[RequestGroup],
) -> dict[str, list[tuple[KeyframeRequest, RequestGroup]]]:
    """Resolve per-channel/per-slot conflicts.

    Returns a mapping ``channel -> [(request, winning_group), ...]`` with at most one
    survivor per slot and preserving the group each request originated from.
    """
    # per-channel per-slot winner candidate
    best: dict[str, dict[int, tuple[tuple[int, int], int, KeyframeRequest, RequestGroup]]] = {}
    for group_index, group in enumerate(groups):
        rank = group_rank(len(group.channel_names), group.tree_depth)
        for channel_name, requests in group.requests.items():
            if channel_name not in group.channel_names:
                continue
            per_slot = best.setdefault(channel_name, {})
            for req in requests:
                slot = int(req.timestep_40hz)
                existing = per_slot.get(slot)
                # Tie-break: smaller rank wins; otherwise earlier group index wins.
                candidate = (rank, group_index, req, group)
                if existing is None or candidate < existing:
                    per_slot[slot] = candidate
    out: dict[str, list[tuple[KeyframeRequest, RequestGroup]]] = {}
    for channel_name, per_slot in best.items():
        ordered = sorted(per_slot.items(), key=lambda kv: kv[0])
        out[channel_name] = [(entry[2], entry[3]) for _, entry in ordered]
    return out


def _dedupe_and_sort(
    stream: list[tuple[KeyframeRequest, RequestGroup]],
) -> list[tuple[KeyframeRequest, RequestGroup]]:
    """Return the stream sorted by slot (already de-duplicated per slot in winner step)."""
    return sorted(stream, key=lambda rg: int(rg[0].timestep_40hz))


def _collect_insertion_slots(
    channel_name: str,
    request_stream: list[tuple[KeyframeRequest, RequestGroup]],
    winners: dict[str, list[tuple[KeyframeRequest, RequestGroup]]],
) -> set[int]:
    """Collect timesteps at which sibling channels have events inside this channel's segments.

    An "inner event" is an event whose slot is strictly between two consecutive events
    on the current channel. Only sibling channels that share a request group with the
    bracketing event on this channel contribute insertions.
    """
    own_slots = {int(req.timestep_40hz) for req, _ in request_stream}
    sibling_slots: set[int] = set()
    if len(request_stream) < 2:
        return sibling_slots
    for i in range(len(request_stream) - 1):
        prev_req, prev_group = request_stream[i]
        nxt_req, nxt_group = request_stream[i + 1]
        prev_slot = int(prev_req.timestep_40hz)
        nxt_slot = int(nxt_req.timestep_40hz)
        if nxt_slot <= prev_slot + 1:
            continue
        sibling_names = (prev_group.channel_names | nxt_group.channel_names) - {channel_name}
        for sibling in sibling_names:
            sibling_stream = winners.get(sibling)
            if not sibling_stream:
                continue
            for sib_req, _ in sibling_stream:
                slot = int(sib_req.timestep_40hz)
                if prev_slot < slot < nxt_slot and slot not in own_slots:
                    sibling_slots.add(slot)
    return sibling_slots


def _materialise(
    spec: ChannelSpec,
    request_stream: list[tuple[KeyframeRequest, RequestGroup]],
    insertion_slots: set[int],
) -> list[KeyFrame]:
    """Build :class:`KeyFrame` instances from the surviving requests and sibling-triggered inserts."""
    frames: list[KeyFrame] = []
    slot_to_frame: dict[int, KeyFrame] = {}
    for i, (req, _group) in enumerate(request_stream):
        slot = int(req.timestep_40hz)
        frame = make_frame(spec, slot, req.transition, req.requested_value)
        slot_to_frame[slot] = frame
        frames.append(frame)
        if i + 1 >= len(request_stream):
            continue
        nxt_req, _ = request_stream[i + 1]
        nxt_slot = int(nxt_req.timestep_40hz)
        if nxt_slot <= slot + 1:
            continue
        prev_state_full = make_state(spec, req.transition, req.requested_value)
        nxt_state_full = make_state(spec, nxt_req.transition, nxt_req.requested_value)
        if curves.is_compatible(prev_state_full, nxt_state_full):
            segment_transition = req.transition
        else:
            segment_transition = TransferFunction.LINEAR
        for mid_slot in sorted(s for s in insertion_slots if slot < s < nxt_slot):
            rel = (mid_slot - slot) / float(nxt_slot - slot)
            try:
                mid_value = curves.value_at(rel, prev_state_full, nxt_state_full, segment_transition)
            except ValueError:
                mid_value = curves.value_at(rel, prev_state_full, nxt_state_full, TransferFunction.LINEAR)
            mid_frame = make_frame(spec, mid_slot, segment_transition, mid_value)
            slot_to_frame[mid_slot] = mid_frame
            frames.append(mid_frame)
    return _collapse_same_slot(frames)


def _collapse_same_slot(frames: list[KeyFrame]) -> list[KeyFrame]:
    """Keep only the last frame per 40 Hz slot, preserving insertion order within a slot."""
    by_slot: dict[int, KeyFrame] = {}
    for kf in frames:
        by_slot[slot_from_seconds(kf.timestamp)] = kf
    ordered_slots = sorted(by_slot.keys())
    return [by_slot[s] for s in ordered_slots]
