"""Property ABC and shared helpers for the property-based cue vfilter (WP4)."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec
    from model.virtual_filters.property_cues.distribution import Distribution
    from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest


TIMESTEPS_PER_SECOND = 40


def seconds_to_timesteps(seconds: float) -> int:
    """Convert a seconds offset to a signed 40 Hz timestep count."""
    return int(round(seconds * TIMESTEPS_PER_SECOND))


def child_start_timestep(
    step_start_40hz: int,
    distribution: Distribution,
    child_index: int,
) -> int:
    """Return the absolute start timestep for ``child_index`` under ``distribution``."""
    return step_start_40hz + seconds_to_timesteps(distribution.delay_for_child(child_index))


class Property(abc.ABC):
    """ABC for a settable property on a step node (fixture, group or segment).

    Concrete properties hold the user-dialed values and emit
    :class:`KeyframeRequest` streams for the channels they own.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Output channels owned by this property (unqualified names)."""

    @abc.abstractmethod
    def generate_requests(
        self,
        step_start_40hz: int,
        step_duration_40hz: int,
        child_index: int,
        distribution: Distribution,
    ) -> dict[str, list[KeyframeRequest]]:
        """Produce keyframe requests for a single child of this property.

        Returned timesteps are absolute within the cue (``step_start_40hz`` plus
        the per-child delay in 1/40 s steps).
        """
