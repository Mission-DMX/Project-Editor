"""Low-level primitive emitted by properties and effect presets.

A :class:`KeyframeRequest` is a request for a channel to hold a given
value at a given point in time. The keyframe solver (WP3) collects
requests across properties and resolves them into actual key frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from model.color_hsi import ColorHSI


RequestedValue = Union[float, int, "ColorHSI"]


@dataclass(slots=True, frozen=True, order=True)
class KeyframeRequest:
    """A requested value for a single channel at a specific point in time.

    ``timestep_40hz`` counts 1/40-second intervals from the start of the cue.
    The ordering ``(timestep_40hz, transition, requested_value)`` lets a list
    of requests be sorted deterministically.
    """

    timestep_40hz: int
    requested_value: RequestedValue
    transition: TransferFunction = TransferFunction.LINEAR
