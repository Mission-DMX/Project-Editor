"""Dimmer property for the property-based cue vfilter.

The raw brightness channel is named ``brightness_raw`` so it cannot collide
with the user-facing ``brightness`` port the dimmer post-processing strategy
exposes after wiring it through the float strobe generator. ``_user_facing_outputs``
hides ``brightness_raw`` and synthesises ``brightness`` with the right data
type; the strobe strategy reads from ``…__brightness_raw`` and publishes on
``…__brightness``. See pan/tilt for the same pattern.
"""

from __future__ import annotations

from dataclasses import dataclass

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property

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
        """Return the brightness, strobe-frequency and duty-cycle channel specs."""
        return (
            ChannelSpec(name=_BRIGHTNESS_RAW, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_STROBEFREQ, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_DUTY_CYCLE, data_type=DataType.DT_DOUBLE, default_value="128"),
        )

    def channel_values(self) -> dict[str, float]:
        """Return the authored brightness/strobe/duty values keyed by channel name."""
        return {
            _BRIGHTNESS_RAW: float(self.brightness),
            _STROBEFREQ: float(self.strobefreq),
            _DUTY_CYCLE: float(self.duty_cycle),
        }
