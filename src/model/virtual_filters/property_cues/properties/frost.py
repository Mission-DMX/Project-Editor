"""Frost property for the property-based cue vfilter."""

from __future__ import annotations

from dataclasses import dataclass

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property

_FROST_INTENSITY = "frost_intensity"


@dataclass(slots=True)
class FrostProperty(Property):
    """Frost intensity (continuous 8-bit)."""

    frost_intensity: int = 0
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Return the single 8-bit frost-intensity channel spec."""
        return (ChannelSpec(name=_FROST_INTENSITY, data_type=DataType.DT_8_BIT),)

    def channel_values(self) -> dict[str, int]:
        """Return the authored frost intensity keyed by channel name."""
        return {_FROST_INTENSITY: int(self.frost_intensity)}
