"""Render an :class:`EffectPreset` into concrete :class:`KeyframeRequest` streams."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import TemplateError

from controller.utils.jinja_math import get_math_enabled_jinja_env
from model.color_hsi import ColorHSI
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest
from model.virtual_filters.property_cues.presets.model import (
    PresetHintType,
)

if TYPE_CHECKING:
    from jinja2 import Environment

    from model.virtual_filters.property_cues.presets.model import (
        EffectPreset,
        PresetHintSpec,
    )


def evaluate_preset(
    preset: EffectPreset,
    hint_values: dict[str, float | int | str],
    step_start_40hz: int,
    step_duration_40hz: int,
    per_child_delay_seconds: float,
    default_transition: TransferFunction = TransferFunction.LINEAR,
) -> dict[str, list[KeyframeRequest]]:
    """Render ``preset`` into keyframe requests across the preset's channels.

    The kf-requests entries are walked repeatedly until the cumulative duration
    covers ``step_duration_40hz / 40`` seconds. Entries that would start past
    the step duration are truncated.
    """
    if not preset.kf_requests:
        return {}
    merged_hints = _merge_hint_values(preset.hints, hint_values)
    env = get_math_enabled_jinja_env()
    results: dict[str, list[KeyframeRequest]] = {}
    step_duration_seconds = step_duration_40hz / 40.0
    cursor_seconds = 0.0
    entry_count = len(preset.kf_requests)
    index = 0
    # ``index`` wraps modulo entry_count to loop; we stop as soon as the cursor
    # has reached (or passed) the step duration so a preset shorter than the
    # step repeats and a preset longer than the step gets truncated.
    while cursor_seconds < step_duration_seconds:
        entry = preset.kf_requests[index % entry_count]
        timestep = round((cursor_seconds + per_child_delay_seconds) * 40) + step_start_40hz
        for channel_name, expression in entry.channel_exprs.items():
            value = _render_channel_value(env, expression, merged_hints)
            request = KeyframeRequest(
                timestep_40hz=timestep,
                requested_value=value,
                transition=default_transition,
            )
            results.setdefault(channel_name, []).append(request)
        duration_seconds = _render_duration(env, entry.duration_expr, merged_hints)
        cursor_seconds += duration_seconds
        index += 1
        if duration_seconds <= 0:
            # A non-positive duration would loop forever; stop after one pass
            # so a malformed preset cannot hang the editor.
            break
    for requests in results.values():
        requests.sort()
    return results


def _merge_hint_values(
    hints: tuple[PresetHintSpec, ...],
    provided: dict[str, float | int | str],
) -> dict[str, float | int | str]:
    merged: dict[str, float | int | str] = {}
    known_ids = {hint.id for hint in hints}
    unknown = set(provided) - known_ids
    if unknown:
        raise ValueError(f"Unknown hint ids: {sorted(unknown)}")
    for hint in hints:
        merged[hint.id] = provided.get(hint.id, hint.default)
    return merged


def _render_duration(
    env: Environment,
    expression: str,
    hint_values: dict[str, float | int | str],
) -> float:
    try:
        rendered = env.from_string(expression).render(hint_values)
    except TemplateError as exc:
        raise ValueError(f"Failed to render duration expression {expression!r}: {exc}") from exc
    try:
        return float(rendered)
    except ValueError as exc:
        raise ValueError(
            f"Duration expression {expression!r} rendered to non-numeric value {rendered!r}"
        ) from exc


def _render_channel_value(
    env: Environment,
    expression: str,
    hint_values: dict[str, float | int | str],
) -> float | ColorHSI:
    try:
        rendered = env.from_string(expression).render(hint_values)
    except TemplateError as exc:
        raise ValueError(f"Failed to render channel expression {expression!r}: {exc}") from exc
    stripped = rendered.strip()
    if stripped.count(",") >= 2:
        try:
            return ColorHSI.from_filter_str(stripped, strict=True)
        except ValueError:
            # Fall through to numeric parsing — the comma count was coincidental.
            pass
    try:
        return float(stripped)
    except ValueError as exc:
        raise ValueError(
            f"Channel expression {expression!r} rendered to non-numeric value {rendered!r}"
        ) from exc
