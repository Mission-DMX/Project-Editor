"""Per-channel keyframe stream builder.

Collapses the former ``_select_winners`` / ``_dedupe_and_sort`` /
``_materialise`` / ``_collapse_same_slot`` cascade into a single
:meth:`KeyframeSolver.solve` pass. The pipeline below :meth:`solve` is now:

1. Walk every :class:`RequestGroup` in authoring order, keeping the latest
   request at each (channel, slot) tuple -- precedence between step- and
   fixture-level assignments is resolved upstream in :func:`_collect_cue`,
   so "last emitted wins" is the right rule for any residual ties.
2. Materialise one :class:`KeyFrame` per surviving request using the
   channel's :class:`ChannelSpec` to pick the state subclass.
3. Return one :class:`SolvedChannel` per channel with a spec; channels that
   received requests but have no spec (an unsupported dimmer ask on a
   gobo-only fixture, for instance) are silently dropped.

Cross-channel interpolation at slots this channel does not touch is handled
later in :func:`_native_builder._state_for` using the next frame's transition.
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

    ``origin_property`` carries the property id ("dimmer", "position", ...) the
    group was emitted for. The solver uses it to resolve cross-property
    collisions deterministically: when two groups write to the same channel
    at the same slot, the one whose ``origin_property`` matches the channel's
    :attr:`ChannelSpec.capability` wins. This prevents a Position preset's
    incidental brightness write from stealing the output from an explicit
    Dimmer assignment regardless of authoring order.
    """

    origin_label: str
    requests: dict[str, list[KeyframeRequest]]
    origin_property: str | None = None


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

        Collision rule: for every (channel, slot) that multiple groups wrote,
        the request whose group's ``origin_property`` matches the channel's
        ``capability`` wins. This makes cross-property overlaps (a Position
        preset that also writes brightness, for instance) resolve toward the
        channel's owning property regardless of authoring order. Among
        same-property or unknown-property matches the latest emission wins.
        """
        # Pass 1: walk groups in emission order, keeping the best request per
        # (channel, slot). "Best" prefers the request whose group matches the
        # channel's owning capability; among equal matches, later wins.
        best_per_slot: dict[str, dict[int, tuple[int, KeyframeRequest]]] = {}
        for group in inp.groups:
            origin = group.origin_property
            for channel_name, requests in group.requests.items():
                spec = inp.channel_specs.get(channel_name)
                channel_cap = spec.capability if spec is not None else None
                score = _match_score(origin, channel_cap)
                per_slot = best_per_slot.setdefault(channel_name, {})
                for req in requests:
                    slot = int(req.timestep_40hz)
                    existing = per_slot.get(slot)
                    # Later emissions tie-break against existing with the
                    # same score (last-write-wins within a tier).
                    if existing is None or score >= existing[0]:
                        per_slot[slot] = (score, req)

        # Pass 2: materialise frames for channels with a known spec.
        result: dict[str, SolvedChannel] = {}
        for channel_name, per_slot in best_per_slot.items():
            spec = inp.channel_specs.get(channel_name)
            if spec is None:
                continue
            frames: list[KeyFrame] = [
                make_frame(spec, slot, per_slot[slot][1].transition, per_slot[slot][1].requested_value)
                for slot in sorted(per_slot)
            ]
            if frames:
                result[channel_name] = SolvedChannel(name=channel_name, frames=frames)
        return result


def _match_score(origin_property: str | None, channel_capability: str | None) -> int:
    """Return the precedence tier for a request on a channel.

    Returns a strictly higher score when the group's originating property
    matches the channel's owning capability, so the matching request wins
    over any cross-property write regardless of authoring order. Unknown
    origins sit between "no match" and "match".
    """
    if origin_property is None:
        return 1
    if channel_capability is None:
        return 1
    return 2 if origin_property == channel_capability else 0
