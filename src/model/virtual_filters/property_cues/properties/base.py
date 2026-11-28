"""Property ABC and shared helpers for the property-based cue vfilter."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec
    from model.virtual_filters.property_cues.distribution import Distribution


TIMESTEPS_PER_SECOND = 40


def seconds_to_timesteps(seconds: float) -> int:
    """Convert a seconds offset to a signed 40 Hz timestep count."""
    return round(seconds * TIMESTEPS_PER_SECOND)


def child_start_timestep(
    step_start_40hz: int,
    distribution: Distribution,
    child_index: int,
    step_duration_40hz: int | None = None,
) -> int:
    """Return the absolute start timestep for ``child_index`` under ``distribution``.

    When ``step_duration_40hz`` is supplied the delay is clamped so that the
    emitted keyframe still lands inside the step: a delay longer than the
    step would otherwise push the keyframe past the step boundary, where
    it never becomes the authored value before the next step's keyframe
    arrives and the fixture appears to skip the step entirely.
    """
    delay_ticks = seconds_to_timesteps(distribution.delay_for_child(child_index))
    if step_duration_40hz is not None and step_duration_40hz > 0:
        # Clamp to one tick before the step ends so the authored value still
        # has at least one 40 Hz slot of effect before the next step takes
        # over; a delay exactly equal to the step would otherwise collide
        # with the next step's own start keyframe.
        delay_ticks = max(0, min(delay_ticks, int(step_duration_40hz) - 1))
    return step_start_40hz + delay_ticks


class Property(abc.ABC):
    """ABC for a settable property on a step node (fixture, group or segment).

    Concrete properties hold the user-dialed values and emit
    :class:`KeyframeRequest` streams for the channels they own. The default
    :meth:`generate_requests` builds one request per channel at the same
    start tick -- subclasses only have to implement :meth:`channel_values`
    returning ``{channel_name: value}``. Properties with dynamic channel
    shapes (gobo wheel count, colour segment count) still override
    :meth:`channel_values` to enumerate the channels their spec would publish.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Output channels owned by this property (unqualified names)."""

    @abc.abstractmethod
    def channel_values(self) -> dict[str, Any]:
        """Return the current authored value for each channel in :attr:`channel_specs`."""

    def generate_requests(
        self,
        step_start_40hz: int,
        step_duration_40hz: int,
        child_index: int,
        distribution: Distribution,
    ) -> dict[str, list[KeyframeRequest]]:
        """Produce keyframe requests for a single child of this property.

        One request per entry returned by :meth:`channel_values`, emitted at
        the step's start tick plus the per-child distribution delay. Discrete
        channels (``spec.discrete``, see L26) override the property's
        transition with :attr:`TransferFunction.EDGE` so wheel-slot values
        don't walk through intermediates during a fade.
        """
        start = child_start_timestep(
            step_start_40hz, distribution, child_index, step_duration_40hz,
        )
        values = self.channel_values()
        transition = getattr(self, "transition", TransferFunction.LINEAR)
        discrete_locals = {spec.name for spec in self.channel_specs if spec.discrete}
        requests: dict[str, list[KeyframeRequest]] = {}
        for name, value in values.items():
            channel_transition = TransferFunction.EDGE if name in discrete_locals else transition
            requests[name] = [KeyframeRequest(
                timestep_40hz=start,
                requested_value=value,
                transition=channel_transition,
            )]
        return requests
