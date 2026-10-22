"""Colour property for the property-based cue vfilter (WP4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest
from model.virtual_filters.property_cues.properties.base import Property, child_start_timestep

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.distribution import Distribution

_COLOR = "color"


def _default_colour() -> ColorHSI:
    return ColorHSI(0.0, 0.0, 0.0)


@dataclass(slots=True)
class ColourProperty(Property):
    """HSI colour of a fixture."""

    color: ColorHSI = field(default_factory=_default_colour)
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        return (ChannelSpec(name=_COLOR, data_type=DataType.DT_COLOR),)

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
            _COLOR: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=self.color,
                    transition=self.transition,
                ),
            ],
        }
