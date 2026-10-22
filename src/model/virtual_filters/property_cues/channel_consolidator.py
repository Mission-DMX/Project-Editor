"""Collapse output channels that resolve to identical keyframe streams (WP3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from model.color_hsi import ColorHSI
from model.filter_data.cues.cue import (
    KeyFrame,
    StateColor,
    StateDouble,
    StateEightBit,
    StateSixteenBit,
)

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec


@dataclass(slots=True, frozen=True)
class ConsolidationMap:
    """Mapping from virtual port id to canonical real port id.

    Virtual ports that were collapsed into another one point to the surviving channel's
    name. Non-collapsed ports map to themselves.
    """

    port_map: dict[str, str]

    def canonical(self, virtual_port_id: str) -> str:
        """Return the canonical port name for ``virtual_port_id``."""
        return self.port_map.get(virtual_port_id, virtual_port_id)


def _frame_signature(frame: KeyFrame) -> tuple:
    """Produce a hashable representation of a frame's content."""
    parts: list = [round(frame.timestamp, 9)]
    for state in frame._states:
        if isinstance(state, StateColor):
            value = state._value
            if isinstance(value, ColorHSI):
                parts.append(("color", value.hue, value.saturation, value.intensity, state._transition_type))
            else:
                parts.append(("color", value, state._transition_type))
        elif isinstance(state, StateEightBit):
            parts.append(("u8", int(state._value), state._transition_type))
        elif isinstance(state, StateSixteenBit):
            parts.append(("u16", int(state._value), state._transition_type))
        elif isinstance(state, StateDouble):
            parts.append(("f", float(state._value), state._transition_type))
        else:
            parts.append(("?", repr(state._value), state._transition_type))
    return tuple(parts)


def _stream_signature(frames: list[KeyFrame]) -> tuple:
    return tuple(_frame_signature(f) for f in frames)


def consolidate(
    per_cue_frames: dict[str, dict[str, list[KeyFrame]]],
    channel_specs: dict[str, ChannelSpec],
    postprocess_signatures: dict[str, str],
) -> ConsolidationMap:
    """Collapse channels whose frames are byte-for-byte identical across ALL cues AND
    whose post-processing signatures match. Pick the alphabetically-earliest channel
    name as the canonical survivor in each equivalence class.
    """
    channel_names = sorted(channel_specs.keys())
    cue_ids = sorted(per_cue_frames.keys())

    def channel_fingerprint(name: str) -> tuple:
        spec = channel_specs[name]
        post = postprocess_signatures.get(name, "")
        per_cue: list = []
        for cue_id in cue_ids:
            cue_map = per_cue_frames.get(cue_id, {})
            frames = cue_map.get(name, [])
            per_cue.append((cue_id, _stream_signature(frames)))
        return (spec.data_type, post, tuple(per_cue))

    buckets: dict[tuple, list[str]] = {}
    for name in channel_names:
        fp = channel_fingerprint(name)
        buckets.setdefault(fp, []).append(name)

    port_map: dict[str, str] = {}
    for members in buckets.values():
        canonical = min(members)
        for member in members:
            port_map[member] = canonical
    return ConsolidationMap(port_map=port_map)
