"""Gobo property for the property-based cue vfilter (WP4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest
from model.virtual_filters.property_cues.properties.base import Property, child_start_timestep

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.distribution import Distribution


def _slot_channel(wheel_index: int) -> str:
    return f"goboslot_{wheel_index}"


def _rotation_channel(wheel_index: int) -> str:
    return f"goborotation_{wheel_index}"


@dataclass(slots=True)
class GoboProperty(Property):
    """Per-wheel gobo slot (discrete) and rotation speed (continuous).

    ``slots`` and ``rotations`` are indexed by wheel index. Entries missing
    from the user-supplied dicts default to 0.
    """

    wheel_count: int = 1
    slots: dict[int, int] = field(default_factory=dict)
    rotations: dict[int, float] = field(default_factory=dict)
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        specs: list[ChannelSpec] = []
        for i in range(self.wheel_count):
            specs.append(ChannelSpec(name=_slot_channel(i), data_type=DataType.DT_8_BIT))
            specs.append(ChannelSpec(name=_rotation_channel(i), data_type=DataType.DT_DOUBLE))
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
        out: dict[str, list[KeyframeRequest]] = {}
        for i in range(self.wheel_count):
            out[_slot_channel(i)] = [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=int(self.slots.get(i, 0)),
                    transition=self.transition,
                ),
            ]
            out[_rotation_channel(i)] = [
                KeyframeRequest(
                    timestep_40hz=start,
                    requested_value=float(self.rotations.get(i, 0.0)),
                    transition=self.transition,
                ),
            ]
        return out
