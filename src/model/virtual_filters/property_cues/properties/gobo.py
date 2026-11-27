"""Gobo property for the property-based cue vfilter."""

from __future__ import annotations

from dataclasses import dataclass, field

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property


def _slot_channel(wheel_index: int) -> str:
    return f"goboslot_{wheel_index}"


def _rotation_channel(wheel_index: int) -> str:
    return f"goborotation_{wheel_index}"


@dataclass(slots=True)
class GoboProperty(Property):
    """Per-wheel gobo slot (discrete) and rotation speed (continuous).

    ``slots`` and ``rotations`` are indexed by wheel index. Entries missing
    from the user-supplied dicts default to 0. S2: the base class builds
    the keyframe requests from :meth:`channel_values`; slot channels are
    marked ``discrete`` on their :class:`ChannelSpec` so the base emits
    them with :attr:`TransferFunction.EDGE` (see L26).
    """

    wheel_count: int = 1
    slots: dict[int, int] = field(default_factory=dict)
    rotations: dict[int, float] = field(default_factory=dict)
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Return a slot and rotation channel spec for each gobo wheel."""
        specs: list[ChannelSpec] = []
        for i in range(self.wheel_count):
            specs.append(ChannelSpec(name=_slot_channel(i), data_type=DataType.DT_8_BIT,
                                     discrete=True))
            specs.append(ChannelSpec(name=_rotation_channel(i), data_type=DataType.DT_DOUBLE))
        return tuple(specs)

    def channel_values(self) -> dict[str, float | int]:
        """Return the authored slot (int) and rotation (float) per wheel."""
        out: dict[str, float | int] = {}
        for i in range(self.wheel_count):
            out[_slot_channel(i)] = int(self.slots.get(i, 0))
            out[_rotation_channel(i)] = float(self.rotations.get(i, 0.0))
        return out
