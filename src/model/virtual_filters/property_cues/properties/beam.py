"""Beam property for the property-based cue vfilter.

Carries zoom, iris and prism (selection + rotation) sub-capabilities. Each
is opt-in via a boolean flag so a fixture that only has zoom (e.g. the
Varytec Hero Wash 640FX) doesn't produce spurious iris / prism output
channels. Dedicated focus lives in :class:`FocusProperty` so wash fixtures
without a focus can skip it entirely.
"""

from __future__ import annotations

from dataclasses import dataclass

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property

_ZOOM = "zoom"
_PRISM_SELECTION = "prism_selection"
_PRISM_ROTATION = "prism_rotation"
_IRIS = "iris"


@dataclass(slots=True)
class BeamProperty(Property):
    """Opt-in zoom / iris / prism channels; omits a channel when its flag is False.

    ``prism_selection`` is marked discrete on its :class:`ChannelSpec` so the
    base :meth:`Property.generate_requests` emits it with
    :attr:`TransferFunction.EDGE` (L26).
    """

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
        """Return the channel specs for the enabled beam sub-channels."""
        specs: list[ChannelSpec] = []
        if self.include_zoom:
            specs.append(ChannelSpec(name=_ZOOM, data_type=DataType.DT_8_BIT))
        if self.include_prism:
            specs.append(ChannelSpec(name=_PRISM_SELECTION, data_type=DataType.DT_8_BIT,
                                     discrete=True))
            specs.append(ChannelSpec(name=_PRISM_ROTATION, data_type=DataType.DT_DOUBLE))
        if self.include_iris:
            specs.append(ChannelSpec(name=_IRIS, data_type=DataType.DT_8_BIT))
        return tuple(specs)

    def channel_values(self) -> dict[str, float | int]:
        """Return the authored value for each enabled beam sub-channel."""
        out: dict[str, float | int] = {}
        if self.include_zoom:
            out[_ZOOM] = int(self.zoom)
        if self.include_prism:
            out[_PRISM_SELECTION] = int(self.prism_selection)
            out[_PRISM_ROTATION] = float(self.prism_rotation)
        if self.include_iris:
            out[_IRIS] = int(self.iris)
        return out
