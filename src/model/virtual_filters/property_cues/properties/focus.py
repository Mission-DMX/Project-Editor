"""Focus property for the property-based cue vfilter.

Kept separate from :class:`BeamProperty` so wash fixtures that have zoom
but no focus do not get a spurious ``__focus`` output channel. The
:class:`view...FocusEditor` writes to the ``"focus"`` property slot.
"""

from __future__ import annotations

from dataclasses import dataclass

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property

_FOCUS = "focus"


@dataclass(slots=True)
class FocusProperty(Property):
    """Single 8-bit focus channel."""

    focus: int = 0
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Return the single 8-bit focus channel spec."""
        return (ChannelSpec(name=_FOCUS, data_type=DataType.DT_8_BIT),)

    def channel_values(self) -> dict[str, int]:
        """Return the authored focus value keyed by channel name."""
        return {_FOCUS: int(self.focus)}
