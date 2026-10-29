"""Deterministic ordering of output channel names.

Channels sort first by fixture prefix (alphabetical), then by property group
following :data:`_PROPERTY_GROUPS`, then by a stable within-property order so
humans can scan the output terminals of the filter node left to right without
hunting for related channels.
"""

from __future__ import annotations

_PROPERTY_GROUPS = (
    "dimmer",
    "position",
    "colour",
    "gobo",
    "beam",
    "focus",
    "frost",
)
_PROPERTY_INDEX = {p: i for i, p in enumerate(_PROPERTY_GROUPS)}
_UNKNOWN_INDEX = len(_PROPERTY_GROUPS)

_LOCAL_NAME_TO_PROPERTY: dict[str, str] = {
    "brightness": "dimmer",
    "strobefreq": "dimmer",
    "duty_cycle": "dimmer",
    "pan": "position",
    "pan_value": "position",
    "pan_curvesel": "position",
    "tilt": "position",
    "tilt_value": "position",
    "tilt_curvesel": "position",
    "color": "colour",
    "zoom": "beam",
    "prism_selection": "beam",
    "prism_rotation": "beam",
    "iris": "beam",
    "focus": "focus",
    "frost_intensity": "frost",
}

_WITHIN_PROPERTY_ORDER: dict[str, tuple[str, ...]] = {
    "dimmer": ("brightness", "strobefreq", "duty_cycle"),
    "position": ("pan", "pan_value", "pan_curvesel", "tilt", "tilt_value", "tilt_curvesel"),
    "colour": ("color",),
    "beam": ("zoom", "prism_selection", "prism_rotation", "iris"),
    "focus": ("focus",),
    "frost": ("frost_intensity",),
}


def _local_sort_tuple(local: str) -> tuple[int, int, int, str]:
    """Return ``(property_index, within_prop_order_a, within_prop_order_b, local)``.

    Gobo channels are keyed off their wheel index so ``goboslot_0`` precedes
    ``goborotation_0`` which precedes ``goboslot_1``, etc.
    """
    if local.startswith("goboslot_"):
        wheel = local[len("goboslot_"):]
        return (_PROPERTY_INDEX["gobo"], int(wheel) if wheel.isdigit() else 9999, 0, local)
    if local.startswith("goborotation_"):
        wheel = local[len("goborotation_"):]
        return (_PROPERTY_INDEX["gobo"], int(wheel) if wheel.isdigit() else 9999, 1, local)
    prop = _LOCAL_NAME_TO_PROPERTY.get(local)
    if prop is None:
        return (_UNKNOWN_INDEX, 0, 0, local)
    order = _WITHIN_PROPERTY_ORDER.get(prop, ())
    try:
        sub = order.index(local)
    except ValueError:
        sub = len(order)
    return (_PROPERTY_INDEX[prop], sub, 0, local)


def channel_sort_key(name: str) -> tuple:
    """Return a sort key for a prefixed channel name (``"<fixture>__<local>"``)."""
    prefix, sep, local = name.partition("__")
    if not sep:
        return (name, _UNKNOWN_INDEX, 0, 0, "")
    return (prefix, *_local_sort_tuple(local))
