"""Metadata describing a single generated output channel of the property-based cue filter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.filter import DataType


@dataclass(slots=True, frozen=True)
class ChannelSpec:
    """A channel the compiled vfilter will produce.

    ``name`` is the sanitised channel name as exposed by the vfilter
    (e.g. ``"MH1__pan_value"``). ``default_value`` is used by the native cue
    filter as the implicit value when a cue does not assign the channel.
    ``discrete`` marks channels (gobo slot, pan/tilt curve selector, prism
    selection) whose values must step instantly between keyframes — the
    emitter forces ``TransferFunction.EDGE`` for them so a slot going 0 → 6
    does not walk through 2/3/4/5 in intermediate ticks (L26).
    """

    name: str
    data_type: DataType
    default_value: str = ""
    discrete: bool = False
