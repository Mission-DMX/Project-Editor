"""Discover and load effect presets from the built-in and user directories."""

from __future__ import annotations

import json
from logging import getLogger
from pathlib import Path

from controller.file.user_data_storage import _USER_STORAGE_PATH
from model.virtual_filters.property_cues.presets.model import (
    EffectPreset,
    PresetHintSpec,
    PresetHintType,
    PresetKeyFrameEntry,
)
from model.virtual_filters.property_cues.presets.schema import validate
from utility import resource_path

logger = getLogger(__name__)


def load_preset_library(
    builtin_dir: str | None = None,
    user_dir: str | None = None,
) -> dict[str, EffectPreset]:
    """Load every ``*.json`` preset from the built-in and user directories.

    - Built-in presets are read from ``resource_path('resources/cuepresets')``
      unless ``builtin_dir`` is given.
    - User presets are read from ``_USER_STORAGE_PATH / 'cuepresets'`` unless
      ``user_dir`` is given.
    - If a user preset's ``name`` matches a built-in preset's ``name`` the
      user copy shadows the built-in in the returned mapping. The built-in
      JSON on disk is left untouched.
    - Malformed JSON files are logged and skipped.
    """
    builtin_path = Path(builtin_dir) if builtin_dir is not None else Path(resource_path("resources/cuepresets"))
    user_path = Path(user_dir) if user_dir is not None else _USER_STORAGE_PATH / "cuepresets"
    library: dict[str, EffectPreset] = {}
    for preset in _load_dir(builtin_path, is_builtin=True):
        library[preset.name] = preset
    for preset in _load_dir(user_path, is_builtin=False):
        library[preset.name] = preset
    return library


def _load_dir(directory: Path, *, is_builtin: bool) -> list[EffectPreset]:
    if not directory.is_dir():
        return []
    presets: list[EffectPreset] = []
    for entry in sorted(directory.iterdir()):
        if entry.suffix.lower() != ".json" or not entry.is_file():
            continue
        preset = _load_file(entry, is_builtin=is_builtin)
        if preset is not None:
            presets.append(preset)
    return presets


def _load_file(path: Path, *, is_builtin: bool) -> EffectPreset | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Failed to read preset file %s: %s", path, exc)
        return None
    try:
        blob = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Malformed preset JSON %s: %s", path, exc)
        return None
    errors = validate(blob)
    if errors:
        logger.warning("Preset %s failed validation: %s", path, "; ".join(errors))
        return None
    try:
        return _build_preset(blob, source_path=str(path), is_builtin=is_builtin)
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Preset %s rejected during construction: %s", path, exc)
        return None


def _build_preset(blob: dict, *, source_path: str, is_builtin: bool) -> EffectPreset:
    hints_blob = blob.get("hints") or []
    hints = tuple(_build_hint(hint) for hint in hints_blob)
    entries_blob = blob.get("kf_requests") or []
    entries = tuple(_build_entry(entry) for entry in entries_blob)
    return EffectPreset(
        name=str(blob["name"]),
        description=str(blob.get("description", "")),
        applies_for=str(blob["applies_for"]),
        hints=hints,
        kf_requests=entries,
        source_path=source_path,
        is_builtin=is_builtin,
    )


def _build_hint(blob: dict) -> PresetHintSpec:
    hint_type = PresetHintType(blob["type"])
    default = blob["default"]
    minimum = blob.get("min")
    maximum = blob.get("max")
    return PresetHintSpec(
        id=str(blob["id"]),
        type=hint_type,
        default=default,
        minimum=float(minimum) if minimum is not None else None,
        maximum=float(maximum) if maximum is not None else None,
    )


def _build_entry(blob: dict) -> PresetKeyFrameEntry:
    channels_blob = blob.get("channels") or {}
    channel_exprs = {str(name): str(expr) for name, expr in channels_blob.items()}
    return PresetKeyFrameEntry(duration_expr=str(blob["duration"]), channel_exprs=channel_exprs)
