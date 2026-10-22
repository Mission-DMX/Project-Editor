"""Position property for the property-based cue vfilter (WP4)."""

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

_PAN_VALUE = "pan_value"
_PAN_CURVESEL = "pan_curvesel"
_TILT_VALUE = "tilt_value"
_TILT_CURVESEL = "tilt_curvesel"

CURVE_DIRECT = 0
CURVE_SIN = 1
CURVE_COS = 2


@dataclass(slots=True)
class PositionProperty(Property):
    """Pan and tilt plus their curve selector channels.

    The curve selector channels are discrete and always treat the distribution
    as an introduction delay only.
    """

    pan_value: float = 0.0
    pan_curvesel: int = CURVE_DIRECT
    tilt_value: float = 0.0
    tilt_curvesel: int = CURVE_DIRECT
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        return (
            ChannelSpec(name=_PAN_VALUE, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_PAN_CURVESEL, data_type=DataType.DT_8_BIT),
            ChannelSpec(name=_TILT_VALUE, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_TILT_CURVESEL, data_type=DataType.DT_8_BIT),
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
            _PAN_VALUE: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.pan_value),
                    transition=self.transition,
                ),
            ],
            _PAN_CURVESEL: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=int(self.pan_curvesel),
                    transition=self.transition,
                ),
            ],
            _TILT_VALUE: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.tilt_value),
                    transition=self.transition,
                ),
            ],
            _TILT_CURVESEL: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=int(self.tilt_curvesel),
                    transition=self.transition,
                ),
            ],
        }
