"""Keyframe transition curves ported from the realtime-fish engine."""

from __future__ import annotations

import math
from typing import Union

from model.color_hsi import ColorHSI
from model.filter_data.cues.cue import (
    State,
    StateColor,
    StateDouble,
    StateEightBit,
    StateSixteenBit,
)
from model.filter_data.transfer_function import TransferFunction

_SIGMOIDAL_OFFSET = 0.0024726231566347743340599073722557624510930726498587540880605924
_SIGMOIDAL_SPAN = 1.0 - 2.0 * _SIGMOIDAL_OFFSET

_NUMERIC_STATES = (StateEightBit, StateSixteenBit, StateDouble)


def _state_value(s: State) -> Union[int, float, ColorHSI]:
    return s._value


def _transition_from(transition: Union[TransferFunction, str]) -> TransferFunction:
    if isinstance(transition, TransferFunction):
        return transition
    return TransferFunction(transition)


def _apply_curve(rel_time: float, transition: TransferFunction) -> float:
    if transition is TransferFunction.LINEAR:
        return rel_time
    if transition is TransferFunction.SIGMOIDAL:
        return (1.0 / (1.0 + math.exp(6.0 - rel_time * 12.0)) - _SIGMOIDAL_OFFSET) / _SIGMOIDAL_SPAN
    if transition is TransferFunction.EASE_IN:
        return rel_time * rel_time
    if transition is TransferFunction.EASE_OUT:
        return 1.0 - ((1.0 - rel_time) * (1.0 - rel_time))
    return rel_time


def _clamp_eight_bit(value: float) -> int:
    rounded = round(value)
    if rounded < 0:
        return 0
    if rounded > 255:
        return 255
    return rounded


def _clamp_sixteen_bit(value: float) -> int:
    rounded = round(value)
    if rounded < 0:
        return 0
    if rounded > 65535:
        return 65535
    return rounded


def _interp_numeric(start: float, end: float, rel_time: float) -> float:
    return (end - start) * rel_time + start


def _shortest_hue_interp(start_hue: float, end_hue: float, rel_time: float) -> float:
    start = start_hue % 360.0
    end = end_hue % 360.0
    diff = end - start
    if diff > 180.0:
        diff -= 360.0
    elif diff < -180.0:
        diff += 360.0
    return (start + diff * rel_time) % 360.0


def _interp_color(start: ColorHSI, end: ColorHSI, rel_time: float) -> ColorHSI:
    hue = _shortest_hue_interp(start.hue, end.hue, rel_time)
    saturation = (end.saturation - start.saturation) * rel_time + start.saturation
    intensity = (end.intensity - start.intensity) * rel_time + start.intensity
    return ColorHSI(hue, saturation, intensity)


def is_compatible(prev: State, nxt: State) -> bool:
    """Return True if the two states share a representation that can be interpolated.

    When False, callers should fall back to linear.
    """
    prev_is_color = isinstance(prev, StateColor)
    next_is_color = isinstance(nxt, StateColor)
    if prev_is_color != next_is_color:
        return False
    prev_is_numeric = isinstance(prev, _NUMERIC_STATES)
    next_is_numeric = isinstance(nxt, _NUMERIC_STATES)
    return prev_is_color or (prev_is_numeric and next_is_numeric)


def _edge_value(t: float, prev: State, nxt: State) -> Union[int, float, ColorHSI]:
    source = prev if t < 1.0 else nxt
    value = _state_value(source)
    if isinstance(nxt, StateEightBit):
        return _clamp_eight_bit(float(value))
    if isinstance(nxt, StateSixteenBit):
        return _clamp_sixteen_bit(float(value))
    if isinstance(nxt, StateDouble):
        return float(value)
    if isinstance(nxt, StateColor):
        return value.copy() if isinstance(value, ColorHSI) else value
    return value


def value_at(
    t: float,
    prev: State,
    nxt: State,
    transition: TransferFunction,
) -> Union[float, int, ColorHSI]:
    """Return the interpolated value at normalised time ``t`` in [0, 1]."""
    if not is_compatible(prev, nxt):
        raise ValueError(
            "Cannot interpolate between incompatible state kinds: "
            f"{type(prev).__name__} and {type(nxt).__name__}"
        )

    transition_enum = _transition_from(transition)

    if t <= 0.0:
        start = _state_value(prev)
        if isinstance(nxt, StateEightBit):
            return _clamp_eight_bit(float(start))
        if isinstance(nxt, StateSixteenBit):
            return _clamp_sixteen_bit(float(start))
        if isinstance(nxt, StateDouble):
            return float(start)
        if isinstance(nxt, StateColor) and isinstance(start, ColorHSI):
            return start.copy()
        return start

    if t >= 1.0:
        end = _state_value(nxt)
        if isinstance(nxt, StateEightBit):
            return _clamp_eight_bit(float(end))
        if isinstance(nxt, StateSixteenBit):
            return _clamp_sixteen_bit(float(end))
        if isinstance(nxt, StateDouble):
            return float(end)
        if isinstance(nxt, StateColor) and isinstance(end, ColorHSI):
            return end.copy()
        return end

    if transition_enum is TransferFunction.EDGE:
        return _edge_value(t, prev, nxt)

    rel_time = _apply_curve(t, transition_enum)

    start_value = _state_value(prev)
    end_value = _state_value(nxt)

    if isinstance(nxt, StateColor):
        return _interp_color(start_value, end_value, rel_time)

    numeric = _interp_numeric(float(start_value), float(end_value), rel_time)
    if isinstance(nxt, StateEightBit):
        return _clamp_eight_bit(numeric)
    if isinstance(nxt, StateSixteenBit):
        return _clamp_sixteen_bit(numeric)
    return numeric
