"""Effect-preset storage format, loader, and evaluator for property-based cues.

A preset bundles a reusable keyframe pattern (e.g. a circle rotation) and the
hints the user can dial in. The loader surfaces built-in presets shipped with
the editor and user presets stored in the local missionDMX data directory.
The evaluator renders a preset into concrete :class:`KeyframeRequest` streams
for a given step duration and per-child delay.
"""

from model.virtual_filters.property_cues.presets.evaluator import evaluate_preset
from model.virtual_filters.property_cues.presets.loader import load_preset_library
from model.virtual_filters.property_cues.presets.model import (
    EffectPreset,
    PresetHintSpec,
    PresetHintType,
    PresetKeyFrameEntry,
)

__all__ = [
    "EffectPreset",
    "PresetHintSpec",
    "PresetHintType",
    "PresetKeyFrameEntry",
    "evaluate_preset",
    "load_preset_library",
]
