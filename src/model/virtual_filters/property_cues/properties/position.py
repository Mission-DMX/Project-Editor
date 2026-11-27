"""Position property for the property-based cue vfilter."""

from __future__ import annotations

from dataclasses import dataclass

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property

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

    The curve-selector channels are discrete (:attr:`ChannelSpec.discrete`)
    and the base :meth:`Property.generate_requests` picks
    :attr:`TransferFunction.EDGE` for them automatically so interpolating
    between e.g. ``CURVE_DIRECT`` and ``CURVE_COS`` never passes through
    ``CURVE_SIN`` mid-step.
    """

    pan_value: float = 0.0
    pan_curvesel: int = CURVE_DIRECT
    tilt_value: float = 0.0
    tilt_curvesel: int = CURVE_DIRECT
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Return the pan/tilt value and curve-selector channel specs."""
        return (
            ChannelSpec(name=_PAN_VALUE, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_PAN_CURVESEL, data_type=DataType.DT_8_BIT, discrete=True),
            ChannelSpec(name=_TILT_VALUE, data_type=DataType.DT_DOUBLE),
            ChannelSpec(name=_TILT_CURVESEL, data_type=DataType.DT_8_BIT, discrete=True),
        )

    def channel_values(self) -> dict[str, float | int]:
        """Return the authored pan/tilt + curve-selector values."""
        return {
            _PAN_VALUE: float(self.pan_value),
            _PAN_CURVESEL: int(self.pan_curvesel),
            _TILT_VALUE: float(self.tilt_value),
            _TILT_CURVESEL: int(self.tilt_curvesel),
        }
