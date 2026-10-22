"""Frost property for the property-based cue vfilter (WP4)."""

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

_FROST_INTENSITY = "frost_intensity"


@dataclass(slots=True)
class FrostProperty(Property):
    """Frost intensity (continuous 8-bit)."""

    frost_intensity: int = 0
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        return (ChannelSpec(name=_FROST_INTENSITY, data_type=DataType.DT_8_BIT),)

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
            _FROST_INTENSITY: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=int(self.frost_intensity),
                    transition=self.transition,
                ),
            ],
        }
