"""Helpers for the keyframe solver (WP3)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.cues.cue import (
    KeyFrame,
    State,
    StateColor,
    StateDouble,
    StateEightBit,
    StateSixteenBit,
)
from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec
    from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest


_SECONDS_PER_SLOT = 1.0 / 40.0


def seconds_from_slot(timestep_40hz: int) -> float:
    """Convert a 40 Hz slot index to seconds."""
    return float(timestep_40hz) * _SECONDS_PER_SLOT


def slot_from_seconds(seconds: float) -> int:
    """Convert a seconds timestamp to a rounded 40 Hz slot index."""
    return round(seconds * 40.0)


def make_state(spec: ChannelSpec, transition: TransferFunction, value: Union[float, ColorHSI]) -> State:
    """Create the ``State`` subclass matching ``spec.data_type`` and populate it."""
    dt = spec.data_type
    transition_str = transition.value if isinstance(transition, TransferFunction) else str(transition)
    if dt == DataType.DT_8_BIT:
        s = StateEightBit(transition_str)
        clamped = round(float(value))
        if clamped < 0:
            clamped = 0
        elif clamped > 255:
            clamped = 255
        s._value = clamped
        return s
    if dt == DataType.DT_16_BIT:
        s = StateSixteenBit(transition_str)
        clamped = round(float(value))
        if clamped < 0:
            clamped = 0
        elif clamped > 65535:
            clamped = 65535
        s._value = clamped
        return s
    if dt == DataType.DT_DOUBLE:
        s = StateDouble(transition_str)
        s._value = float(value)
        return s
    if dt == DataType.DT_COLOR:
        s = StateColor(transition_str)
        if isinstance(value, ColorHSI):
            s._value = value.copy()
        else:
            s._value = ColorHSI(float(value), 0.0, 0.0)
        return s
    raise ValueError(f"Unsupported data type: {dt}")


def make_frame(spec: ChannelSpec, timestep_40hz: int, transition: TransferFunction,
               value: Union[float, ColorHSI]) -> KeyFrame:
    """Build a single-state ``KeyFrame`` for channel ``spec``."""
    kf = KeyFrame(None)
    kf.timestamp = seconds_from_slot(timestep_40hz)
    kf.append_state(make_state(spec, transition, value))
    return kf


def group_rank(channel_count: int, tree_depth: int) -> tuple[int, int]:
    """Return a comparable rank used for conflict resolution.

    Groups with fewer channels (more specialised) are preferred.
    Among equally-specialised groups the deeper one wins. The rank is used with
    ``min`` so smaller tuples win.
    """
    return (channel_count, -tree_depth)
