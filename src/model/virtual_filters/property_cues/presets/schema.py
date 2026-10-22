"""JSON schema and hand-written validator for the effect preset format."""

from __future__ import annotations

PRESET_JSON_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EffectPreset",
    "type": "object",
    "required": ["name", "applies_for", "kf_requests"],
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "applies_for": {"type": "string"},
        "hints": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "default"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"enum": ["float", "int", "color"]},
                    "default": {},
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                },
            },
        },
        "kf_requests": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["duration", "channels"],
                "properties": {
                    "duration": {"type": "string"},
                    "channels": {"type": "object", "additionalProperties": {"type": "string"}},
                },
            },
        },
    },
}

_ALLOWED_HINT_TYPES = {"float", "int", "color"}


def validate(blob: dict) -> list[str]:
    """Validate a preset JSON blob against :data:`PRESET_JSON_SCHEMA`.

    Returns a list of human-readable error messages; empty if the blob is valid.
    """
    errors: list[str] = []
    if not isinstance(blob, dict):
        return ["Preset must be a JSON object at the top level."]
    for key in ("name", "applies_for", "kf_requests"):
        if key not in blob:
            errors.append(f"Missing required field '{key}'.")
    if "name" in blob and not isinstance(blob["name"], str):
        errors.append("Field 'name' must be a string.")
    if "description" in blob and not isinstance(blob["description"], str):
        errors.append("Field 'description' must be a string.")
    if "applies_for" in blob and not isinstance(blob["applies_for"], str):
        errors.append("Field 'applies_for' must be a string.")
    hints = blob.get("hints")
    if hints is not None:
        if not isinstance(hints, list):
            errors.append("Field 'hints' must be an array.")
        else:
            for index, hint in enumerate(hints):
                errors.extend(_validate_hint(hint, index))
    if "kf_requests" in blob:
        kf_requests = blob["kf_requests"]
        if not isinstance(kf_requests, list):
            errors.append("Field 'kf_requests' must be an array.")
        else:
            for index, entry in enumerate(kf_requests):
                errors.extend(_validate_kf_entry(entry, index))
    return errors


def _validate_hint(hint: object, index: int) -> list[str]:
    prefix = f"hints[{index}]"
    if not isinstance(hint, dict):
        return [f"{prefix} must be an object."]
    errors: list[str] = []
    for key in ("id", "type", "default"):
        if key not in hint:
            errors.append(f"{prefix} missing required field '{key}'.")
    if "id" in hint and not isinstance(hint["id"], str):
        errors.append(f"{prefix}.id must be a string.")
    if "type" in hint and hint["type"] not in _ALLOWED_HINT_TYPES:
        errors.append(f"{prefix}.type must be one of {sorted(_ALLOWED_HINT_TYPES)}.")
    for bound in ("min", "max"):
        if bound in hint and not isinstance(hint[bound], (int, float)):
            errors.append(f"{prefix}.{bound} must be a number.")
    return errors


def _validate_kf_entry(entry: object, index: int) -> list[str]:
    prefix = f"kf_requests[{index}]"
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object."]
    errors: list[str] = []
    for key in ("duration", "channels"):
        if key not in entry:
            errors.append(f"{prefix} missing required field '{key}'.")
    if "duration" in entry and not isinstance(entry["duration"], str):
        errors.append(f"{prefix}.duration must be a string expression.")
    if "channels" in entry:
        channels = entry["channels"]
        if not isinstance(channels, dict):
            errors.append(f"{prefix}.channels must be an object.")
        else:
            for channel_name, expr in channels.items():
                if not isinstance(channel_name, str):
                    errors.append(f"{prefix}.channels keys must be strings.")
                if not isinstance(expr, str):
                    errors.append(f"{prefix}.channels.{channel_name} must be a string expression.")
    return errors
