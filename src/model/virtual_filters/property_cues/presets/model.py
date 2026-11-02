"""Dataclasses describing an effect preset in memory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PresetHintType(Enum):
    """Supported hint value types.

    Hints with type ``COLOR`` encode their default as an ``"h,s,i"`` string
    consumable by :meth:`ColorHSI.from_filter_str`.
    """

    FLOAT = "float"
    INT = "int"
    COLOR = "color"


@dataclass(slots=True, frozen=True)
class PresetHintSpec:
    """Metadata for a single hint the user can dial in on a preset."""

    id: str
    type: PresetHintType
    default: float | int | str
    minimum: float | None = None
    maximum: float | None = None


@dataclass(slots=True, frozen=True)
class PresetKeyFrameEntry:
    """One step of the preset's kf-requests array.

    ``duration_expr`` is a jinja expression that renders to a float number of
    seconds. ``channel_exprs`` maps channel names to jinja expressions whose
    rendered output is either a numeric string or an ``"h,s,i"`` color string.
    """

    duration_expr: str
    channel_exprs: dict[str, str]


@dataclass(slots=True, frozen=True)
class EffectPreset:
    """A loaded effect preset ready for evaluation.

    ``source_path`` is kept for round-trip editing and so the UI can show
    where a preset lives. ``is_builtin`` distinguishes shipped presets from
    user-authored ones.
    """

    name: str
    description: str
    applies_for: str
    hints: tuple[PresetHintSpec, ...]
    kf_requests: tuple[PresetKeyFrameEntry, ...]
    source_path: str
    is_builtin: bool
