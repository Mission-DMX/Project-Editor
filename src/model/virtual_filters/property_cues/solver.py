"""Per-channel keyframe stream builder.

S6: collapses the former ``_select_winners`` / ``_dedupe_and_sort`` /
``_materialise`` / ``_collapse_same_slot`` cascade into a single
:meth:`KeyframeSolver.solve` pass. The pipeline below :meth:`solve` is now:

1. Walk every :class:`RequestGroup` in authoring order, keeping the latest
   request at each (channel, slot) tuple -- precedence between step- and
   fixture-level assignments is resolved upstream in :func:`_collect_cue`
   (L6), so "last emitted wins" is the right rule for any residual ties.
2. Materialise one :class:`KeyFrame` per surviving request using the
   channel's :class:`ChannelSpec` to pick the state subclass.
3. Return one :class:`SolvedChannel` per channel with a spec; channels that
   received requests but have no spec (an unsupported dimmer ask on a
   gobo-only fixture, for instance) are silently dropped.

Cross-channel interpolation at slots this channel does not touch is handled
later in :func:`_native_builder._state_for` using the next frame's transition
(F1).
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING

from model.virtual_filters.property_cues.solver_helpers import make_frame

if TYPE_CHECKING:
    from model.filter_data.cues.cue import KeyFrame
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec
    from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest


logger = getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RequestGroup:
    """A set of keyframe requests emitted together by a single property/preset invocation.

    S7: before the per-step precedence resolution moved into
    :func:`_collect_cue` (L6), the solver ranked groups by
    ``(channel_count, tree_depth)`` and used ``channel_names`` as a
    per-channel membership filter. Both roles are obsolete now -- the
    compiler emits one group per (child, pid) per step and the solver just
    deduplicates per slot -- so only ``origin_label`` (diagnostic) and
    ``requests`` (payload) remain.
    """

    origin_label: str
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
    """Flatten a cue's :class:`RequestGroup` stream into per-channel keyframes."""

    def solve(self, inp: SolveInput) -> dict[str, SolvedChannel]:
        """Return one :class:`SolvedChannel` per channel that received any request.

        See the module docstring for the algorithm. Channels without a
        matching :class:`ChannelSpec` in ``inp.channel_specs`` are dropped;
        this is how a preset emitting on a channel the fixture doesn't
        support goes away silently.
        """
        # Pass 1: last-write-wins per (channel, slot) across all groups.
        latest_per_slot: dict[str, dict[int, KeyframeRequest]] = {}
        for group in inp.groups:
            for channel_name, requests in group.requests.items():
                per_slot = latest_per_slot.setdefault(channel_name, {})
                for req in requests:
                    per_slot[int(req.timestep_40hz)] = req

        # Pass 2: materialise frames for channels with a known spec.
        result: dict[str, SolvedChannel] = {}
        for channel_name, per_slot in latest_per_slot.items():
            spec = inp.channel_specs.get(channel_name)
            if spec is None:
                continue
            frames: list[KeyFrame] = [
                make_frame(spec, slot, per_slot[slot].transition, per_slot[slot].requested_value)
                for slot in sorted(per_slot)
            ]
            if frames:
                result[channel_name] = SolvedChannel(name=channel_name, frames=frames)
        return result
