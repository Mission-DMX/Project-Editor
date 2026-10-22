"""Metadata describing a single generated output channel of the property-based cue filter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.filter import DataType


@dataclass(slots=True, frozen=True)
class ChannelSpec:
    """A channel the compiled vfilter will produce.

    ``name`` is the sanitised channel name as exposed by the vfilter
    (e.g. ``"MH1__pan_value"``). ``default_value`` is used by the native cue
    filter as the implicit value when a cue does not assign the channel.
    """

    name: str
    data_type: DataType
    default_value: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)
