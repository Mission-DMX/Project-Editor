"""Low-level primitive emitted by properties and effect presets.

A :class:`KeyframeRequest` is a request for a channel to hold a given
value at a given point in time. The keyframe solver collects requests
across properties and resolves them into actual key frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from model.color_hsi import ColorHSI


RequestedValue = Union[float, int, "ColorHSI"]


@dataclass(slots=True, frozen=True)
class KeyframeRequest:
    """A requested value for a single channel at a specific point in time.

    ``timestep_40hz`` counts 1/40-second intervals from the start of the cue.
    """

    timestep_40hz: int
    requested_value: RequestedValue
    transition: TransferFunction = TransferFunction.LINEAR

    def __lt__(self, other: object) -> bool:
        """Order requests solely by ``timestep_40hz`` (L15).

        The default dataclass ``order=True`` compared the full tuple
        including ``requested_value`` and ``transition``. Neither
        :class:`ColorHSI` nor :class:`TransferFunction` support cross-type
        comparison, so sorting a request stream that mixed types would
        raise ``TypeError`` -- which is exactly how a sibling preset
        emitting two colour requests at the same slot crashed the
        compiler. Ordering by slot alone is enough for all internal
        sorts (solver, evaluator) because the slot is the only
        timeline-relevant attribute.
        """
        if not isinstance(other, KeyframeRequest):
            return NotImplemented
        return self.timestep_40hz < other.timestep_40hz
