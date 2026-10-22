"""Beam property for the property-based cue vfilter (WP4)."""

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

_FOCUS = "focus"
_ZOOM = "zoom"
_PRISM_SELECTION = "prism_selection"
_PRISM_ROTATION = "prism_rotation"
_IRIS = "iris"


@dataclass(slots=True)
class BeamProperty(Property):
    """Focus, zoom, iris, prism selection and prism rotation.

    All channels except ``prism_rotation`` are discrete.
    """

    focus: int = 0
    zoom: int = 0
    prism_selection: int = 0
    prism_rotation: float = 0.0
    iris: int = 0
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        return (
            ChannelSpec(name=_FOCUS, data_type=DataType.DT_8_BIT),
            ChannelSpec(name=_ZOOM, data_type=DataType.DT_8_BIT),
            ChannelSpec(name=_PRISM_SELECTION, data_type=DataType.DT_8_BIT),
            ChannelSpec(name=_PRISM_ROTATION, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_IRIS, data_type=DataType.DT_8_BIT),
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
            _FOCUS: [KeyframeRequest(timestep_40hz=start, requested_value=int(self.focus), transition=self.transition)],
            _ZOOM: [KeyframeRequest(timestep_40hz=start, requested_value=int(self.zoom), transition=self.transition)],
            _PRISM_SELECTION: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=int(self.prism_selection),
                    transition=self.transition,
                ),
            ],
            _PRISM_ROTATION: [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.prism_rotation),
                    transition=self.transition,
                ),
            ],
            _IRIS: [KeyframeRequest(timestep_40hz=start, requested_value=int(self.iris), transition=self.transition)],
        }
