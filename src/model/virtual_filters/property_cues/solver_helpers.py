"""Helpers for the keyframe solver.

``make_state`` and ``_dedupe_and_sort`` / ``_collapse_same_slot`` / the
``slot_to_frame`` dict were removed when :class:`KeyframeSolver.solve`
collapsed to a single pass. Only the small time-conversion helpers and the
``make_frame`` factory remain -- they are still used by the compiler's L5
closing-keyframe pass, the native builder, and the solver tests.
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


def make_frame(spec: ChannelSpec, timestep_40hz: int, transition: TransferFunction,
               value: Union[float, ColorHSI]) -> KeyFrame:
    """Build a single-state ``KeyFrame`` for channel ``spec``."""
    return KeyFrame.at(
        seconds_from_slot(timestep_40hz),
        states=[State.from_value(spec.data_type, transition, value)],
    )
