"""Beam property for the property-based cue vfilter.

Carries zoom, iris and prism (selection + rotation) sub-capabilities. Each
is opt-in via a boolean flag so a fixture that only has zoom (e.g. the
Varytec Hero Wash 640FX) doesn't produce spurious iris / prism output
channels. Dedicated focus lives in :class:`FocusProperty` so wash fixtures
without a focus can skip it entirely.
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

_ZOOM = "zoom"
_PRISM_SELECTION = "prism_selection"
_PRISM_ROTATION = "prism_rotation"
_IRIS = "iris"


@dataclass(slots=True)
class BeamProperty(Property):
    """Opt-in zoom / iris / prism channels; omits a channel when its flag is False."""

    zoom: int = 0
    prism_selection: int = 0
    prism_rotation: float = 0.0
    iris: int = 0
    include_zoom: bool = True
    include_iris: bool = True
    include_prism: bool = True
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        specs: list[ChannelSpec] = []
        if self.include_zoom:
            specs.append(ChannelSpec(name=_ZOOM, data_type=DataType.DT_8_BIT))
        if self.include_prism:
            specs.append(ChannelSpec(name=_PRISM_SELECTION, data_type=DataType.DT_8_BIT))
            specs.append(ChannelSpec(name=_PRISM_ROTATION, data_type=DataType.DT_DOUBLE))
        if self.include_iris:
            specs.append(ChannelSpec(name=_IRIS, data_type=DataType.DT_8_BIT))
        return tuple(specs)

    def generate_requests(
        self,
        step_start_40hz: int,
        step_duration_40hz: int,
        child_index: int,
        distribution: Distribution,
    ) -> dict[str, list[KeyframeRequest]]:
        del step_duration_40hz
        start = child_start_timestep(step_start_40hz, distribution, child_index)
        requests: dict[str, list[KeyframeRequest]] = {}
        if self.include_zoom:
            requests[_ZOOM] = [KeyframeRequest(
                timestep_40hz=start, requested_value=int(self.zoom), transition=self.transition,
            )]
        if self.include_prism:
            requests[_PRISM_SELECTION] = [KeyframeRequest(
                timestep_40hz=start, requested_value=int(self.prism_selection),
                transition=self.transition,
            )]
            requests[_PRISM_ROTATION] = [KeyframeRequest(
                timestep_40hz=start, requested_value=float(self.prism_rotation),
                transition=self.transition,
            )]
        if self.include_iris:
            requests[_IRIS] = [KeyframeRequest(
                timestep_40hz=start, requested_value=int(self.iris), transition=self.transition,
            )]
        return requests
