"""Helpers for the keyframe solver (WP3).

``make_state`` / ``make_frame`` are kept as thin wrappers over
:meth:`State.from_value` / :meth:`KeyFrame.at` so callers that still import
them don't have to be updated at the same time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from model.filter_data.cues.cue import KeyFrame, State

if TYPE_CHECKING:
    from model.color_hsi import ColorHSI
    from model.filter_data.transfer_function import TransferFunction
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec


_SECONDS_PER_SLOT = 1.0 / 40.0


def seconds_from_slot(timestep_40hz: int) -> float:
    """Convert a 40 Hz slot index to seconds."""
    return float(timestep_40hz) * _SECONDS_PER_SLOT


def slot_from_seconds(seconds: float) -> int:
    """Convert a seconds timestamp to a rounded 40 Hz slot index."""
    return round(seconds * 40.0)


def make_state(spec: ChannelSpec, transition: TransferFunction, value: Union[float, ColorHSI]) -> State:
    """Create the ``State`` subclass matching ``spec.data_type`` and populate it."""
    return State.from_value(spec.data_type, transition, value)


def make_frame(spec: ChannelSpec, timestep_40hz: int, transition: TransferFunction,
               value: Union[float, ColorHSI]) -> KeyFrame:
    """Build a single-state ``KeyFrame`` for channel ``spec``."""
    return KeyFrame.at(
        seconds_from_slot(timestep_40hz),
        states=[State.from_value(spec.data_type, transition, value)],
    )


def group_rank(channel_count: int, tree_depth: int) -> tuple[int, int]:
    """Return a comparable rank used for conflict resolution.

    Groups with fewer channels (more specialised) are preferred.
    Among equally-specialised groups the deeper one wins. The rank is used with
    ``min`` so smaller tuples win.
    """
    return (channel_count, -tree_depth)
