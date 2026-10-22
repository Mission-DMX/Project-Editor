"""Child-index distribution for property keyframe requests.

A :class:`Distribution` turns a child-index (position of a fixture within its
parent group / segment) into an extra start-time offset. Properties use this
offset to spread their keyframes across siblings for chase and wave effects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class DistributionMethod(Enum):
    """How a :class:`Distribution` maps a child-index to a delay offset."""

    CONSTANT = "constant"
    PHASE_LINEAR = "phase_linear"
    PHASE_SIN = "phase_sin"
    PHASE_COS = "phase_cos"
    PHASE_SAW = "phase_saw"


@dataclass(slots=True, frozen=True)
class Distribution:
    """Per-child start-time offset generator.

    ``phase_offset`` is the radians-per-child-index step for the periodic
    methods and the seconds-per-child-index step for :attr:`DistributionMethod.PHASE_LINEAR`.
    ``amplitude`` scales the raw delay function output.

    When :attr:`introduction_delay_only` is set the consumer is expected to
    apply the delay to the start time only and NOT to scale the requested value.
    Discrete-channel properties always treat the distribution this way, regardless
    of this flag.
    """

    method: DistributionMethod = DistributionMethod.CONSTANT
    phase_offset: float = 0.0
    amplitude: float = 1.0
    introduction_delay_only: bool = False

    def delay_for_child(self, child_index: int) -> float:
        """Return the extra start-time offset (seconds) for ``child_index``."""
        if self.method is DistributionMethod.CONSTANT:
            return 0.0
        if self.method is DistributionMethod.PHASE_LINEAR:
            return self.amplitude * self.phase_offset * child_index
        if self.method is DistributionMethod.PHASE_SIN:
            return self.amplitude * math.sin(self.phase_offset * child_index)
        if self.method is DistributionMethod.PHASE_COS:
            return self.amplitude * math.cos(self.phase_offset * child_index)
        if self.method is DistributionMethod.PHASE_SAW:
            fraction = (self.phase_offset * child_index / (2.0 * math.pi)) % 1.0
            return self.amplitude * (fraction - 0.5) * 2.0
        raise ValueError(f"Unknown distribution method: {self.method!r}")
