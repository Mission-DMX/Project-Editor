"""Dimmer property for the property-based cue vfilter (WP4).

The raw brightness channel is named ``brightness_raw`` so it cannot collide
with the user-facing ``brightness`` port the dimmer post-processing strategy
exposes after wiring it through the float strobe generator. ``_user_facing_outputs``
hides ``brightness_raw`` and synthesises ``brightness`` with the right data
type; the strobe strategy reads from ``…__brightness_raw`` and publishes on
``…__brightness``. See pan/tilt for the same pattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest
from model.virtual_filters.property_cues.properties.base import Property, child_start_timestep

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.distribution import Distribution

_BRIGHTNESS_RAW = "brightness_raw"
_STROBEFREQ = "strobefreq"
_DUTY_CYCLE = "duty_cycle"


@dataclass(slots=True)
class DimmerProperty(Property):
    """Dimmer brightness plus strobe frequency and duty cycle.

    ``strobefreq`` doubles as the shutter channel; the shutter UI is a shim over
    this field. ``duty_cycle`` drives the strobe generator's 8-bit duty-cycle
    input (0 = brief ON pulses, 128 = balanced, 255 = brief OFF pulses). All
    three channels share the configured transition.
    """

    brightness: float = 0.0
    strobefreq: float = 0.0
    duty_cycle: float = 128.0
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        return (
            ChannelSpec(name=_BRIGHTNESS_RAW, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_STROBEFREQ, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_DUTY_CYCLE, data_type=DataType.DT_DOUBLE, default_value="128"),
        )

    def generate_requests(
        self,
        step_start_40hz: int,
        step_duration_40hz: int,
        child_index: int,
        distribution: Distribution,
    ) -> dict[str, list[KeyframeRequest]]:
        del step_duration_40hz
        start = child_start_timestep(step_start_40hz, distribution, child_index)
        return {
            _BRIGHTNESS_RAW: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.brightness),
                    transition=self.transition,
                ),
            ],
            _STROBEFREQ: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.strobefreq),
                    transition=self.transition,
                ),
            ],
            _DUTY_CYCLE: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.duty_cycle),
                    transition=self.transition,
                ),
            ],
        }
