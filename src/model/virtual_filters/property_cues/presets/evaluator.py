"""Render an :class:`EffectPreset` into concrete :class:`KeyframeRequest` streams."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from jinja2 import TemplateError

from controller.utils.jinja_math import get_math_enabled_jinja_env
from model.color_hsi import ColorHSI
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest
from model.virtual_filters.property_cues.presets.model import (
    PresetHintType,
)

logger = getLogger(__name__)


# L14: compile each distinct Jinja template once and reuse. The compiler used
# to call ``env.from_string(expression)`` on every (cue, step, child, loop
# iteration) tuple, which for a 12-fixture by 4-step "Circle" preset
# produced ~11k template compilations per rebuild. Caching here makes the
# hot path O(unique_expressions) rather than O(invocations). The cache is
# module-level because the Jinja environment is a singleton and expressions
# never alias across environments. Call :func:`clear_template_cache` from
# :func:`reload_preset_library` so a modified preset re-compiles its exprs.
_TEMPLATE_CACHE: dict[str, object] = {}


def _compile_template(env: Environment, expression: str) -> object:
    """Return a cached compiled Jinja template for ``expression``."""
    cached = _TEMPLATE_CACHE.get(expression)
    if cached is not None:
        return cached
    compiled = env.from_string(expression)
    _TEMPLATE_CACHE[expression] = compiled
    return compiled


def clear_template_cache() -> None:
    """Drop every cached Jinja template.

    Called from :func:`reload_preset_library` so a saved edit to a preset
    doesn't continue to render the pre-edit expressions out of the cache.
    """
    _TEMPLATE_CACHE.clear()

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
    """Return the effective hint values for ``hints`` merging in ``provided``.

    L16: unknown hint ids are logged and dropped instead of raising, so a
    preset that renames or removes a hint doesn't break every cue that
    used to reference it. The declared ``minimum`` and ``maximum`` bounds
    on numeric hints are enforced here: user-supplied values outside the
    range are clamped and the original is logged for traceability.
    """
    merged: dict[str, float | int | str] = {}
    known_ids = {hint.id for hint in hints}
    unknown = set(provided) - known_ids
    if unknown:
        logger.warning(
            "Dropping unknown preset hint ids: %s (preset hints: %s)",
            sorted(unknown), sorted(known_ids),
        )
    for hint in hints:
        raw = provided.get(hint.id, hint.default)
        merged[hint.id] = _clip_hint_value(hint, raw)
    return merged


def _clip_hint_value(
    hint: PresetHintSpec,
    value: float | str,
) -> float | int | str:
    """Clamp ``value`` to the hint's declared ``[minimum, maximum]`` bounds (L16).

    Only numeric hints (float/int) are clamped; colour hints and malformed
    numeric values pass through untouched. A clamp is logged so the user
    can tell whether their authored value made it through verbatim.
    """
    if hint.type is PresetHintType.COLOR:
        return value
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value
    lo = hint.minimum
    hi = hint.maximum
    original = numeric
    if lo is not None and numeric < float(lo):
        numeric = float(lo)
    if hi is not None and numeric > float(hi):
        numeric = float(hi)
    if numeric != original:
        logger.info(
            "Clamped preset hint %s=%r to %r (range [%s, %s])",
            hint.id, original, numeric, lo, hi,
        )
    if hint.type is PresetHintType.INT:
        return round(numeric)
    return numeric


def _render_duration(
    env: Environment,
    expression: str,
    hint_values: dict[str, float | int | str],
) -> float:
    try:
        rendered = _compile_template(env, expression).render(hint_values)
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
        rendered = _compile_template(env, expression).render(hint_values)
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
