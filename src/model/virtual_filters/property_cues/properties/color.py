"""Color property for the property-based cue vfilter.

Supports multi-segment fixtures: ``segment_count == 1`` exposes a single
output channel named ``color`` (so single-pixel fixtures keep their
existing channel-link bindings), ``segment_count > 1`` exposes
``color_0 .. color_{N-1}``. The compiler fills ``segment_count`` from
the fixture discovery; assignments only persist the authored
``colors: {segment_index: ColorHSI}`` map.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties.base import Property

_COLOR = "color"


def color_channel_name(segment_index: int, segment_count: int) -> str:
    """Return the channel name a given segment emits.

    Single-segment fixtures keep the bare ``color`` name so existing
    channel-link bindings resolve. Multi-segment fixtures use the
    indexed form ``color_N``.
    """
    return _COLOR if segment_count <= 1 else f"{_COLOR}_{segment_index}"


def distribute_colors(authored: dict[int, ColorHSI], n: int) -> list[ColorHSI]:
    """Spread K authored colours across N fixture segments.

    Rule (specified by the user):
      * K == 1      → the single colour is applied to every segment.
      * 1 < K < N   → segment *i* gets authored colour ``floor(i·K / N)``.
      * K >= N      → the first N authored colours, one per segment.
      * K == 0      → every segment defaults to black.
    """
    if n <= 0:
        return []
    if not authored:
        return [ColorHSI(0.0, 0.0, 0.0)] * n
    sorted_items = [authored[k] for k in sorted(authored.keys())]
    k = len(sorted_items)
    if k == 1:
        return [sorted_items[0]] * n
    if k >= n:
        return sorted_items[:n]
    return [sorted_items[i * k // n] for i in range(n)]


@dataclass(slots=True)
class ColorProperty(Property):
    """HSI colour of a fixture, with one value per LED/pixel segment."""

    segment_count: int = 1
    colors: dict[int, ColorHSI] = field(default_factory=dict)
    transition: TransferFunction = TransferFunction.LINEAR

    @property
    def channel_specs(self) -> tuple[ChannelSpec, ...]:
        """Return one colour channel spec per LED/pixel segment."""
        count = max(1, int(self.segment_count))
        return tuple(
            ChannelSpec(name=color_channel_name(i, count), data_type=DataType.DT_COLOR)
            for i in range(count)
        )

    def channel_values(self) -> dict[str, ColorHSI]:
        """Return a distributed colour per segment, keyed by channel name.

        dynamic channel count — the base class's ``channel_values``
        contract is satisfied by enumerating one entry per segment from
        :func:`distribute_colors`.
        """
        count = max(1, int(self.segment_count))
        per_segment = distribute_colors(self.colors, count)
        return {
            color_channel_name(i, count): per_segment[i]
            for i in range(count)
        }
