"""Classify fixture capabilities from an OFL definition.

Returns string tags (``"dimmer"``, ``"position"``, ``"colour"``, ``"gobo"``,
``"beam"``, ``"focus"``, ``"frost"``) so callers in different layers can map
them onto whichever enum they use (e.g. the property-cue vfilter's
``EnabledCapability``). Lives in the OFL model package so the discovery
sits next to the OFL types it inspects.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from model.ofl.ofl_fixture import CapabilityType, WheelSlotType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model.ofl.fixture import UsedFixture
    from model.ofl.ofl_fixture import Wheel

logger = getLogger(__name__)


_CAPABILITY_TYPE_TO_TAG: dict[CapabilityType, str] = {
    CapabilityType.COLOR_INTENSITY: "colour",
    CapabilityType.COLOR_PRESET: "colour",
    CapabilityType.COLOR_TEMPERATURE: "colour",
    CapabilityType.PAN: "position",
    CapabilityType.PAN_CONTINUOUS: "position",
    CapabilityType.TILT: "position",
    CapabilityType.TILT_CONTINUOUS: "position",
    CapabilityType.INTENSITY: "dimmer",
    CapabilityType.FOCUS: "focus",
    CapabilityType.ZOOM: "beam",
    CapabilityType.IRIS: "beam",
    CapabilityType.IRIS_EFFECT: "beam",
    CapabilityType.PRISM: "beam",
    CapabilityType.PRISM_ROTATION: "beam",
    CapabilityType.BEAM_ANGLE: "beam",
    CapabilityType.FROST: "frost",
    CapabilityType.FROST_EFFECT: "frost",
}


_GOBO_SLOT_TYPES = frozenset(
    {WheelSlotType.GOBO, WheelSlotType.ANIMATED_GOBO_START, WheelSlotType.ANIMATED_GOBO_END},
)


def _wheels_of(fixture: UsedFixture) -> dict[str, Wheel]:
    """Return the fixture's OFL wheel map (private access to the OFL template)."""
    ofl = getattr(fixture, "_fixture", None)
    return getattr(ofl, "wheels", {}) if ofl is not None else {}


def _capabilities_from_wheels(fixture: UsedFixture) -> set[str]:
    """Inspect wheel slot types directly: GOBO slots → "gobo"; COLOR slots → "colour"."""
    caps: set[str] = set()
    for wheel in _wheels_of(fixture).values():
        for slot in getattr(wheel, "slots", []):
            if slot.type in _GOBO_SLOT_TYPES:
                caps.add("gobo")
            elif slot.type is WheelSlotType.COLOR:
                caps.add("colour")
    return caps


def _tag_for(cap_type: CapabilityType, channel_name: str) -> str | None:
    """Return the capability tag for a single non-wheel OFL capability, or None if unknown."""
    if cap_type == CapabilityType.WHEEL_SLOT:
        return None  # Handled via wheel-slot-type inspection in _capabilities_from_wheels.
    mapped = _CAPABILITY_TYPE_TO_TAG.get(cap_type)
    if mapped is None:
        logger.debug(
            "Capability type %s on channel %r has no capability tag; skipping.",
            cap_type,
            channel_name,
        )
    return mapped


def discover_capabilities(fixtures: Iterable[UsedFixture]) -> set[str]:
    """Union of capability tags derived from channel templates and wheel slot types."""
    result: set[str] = set()
    for fixture in fixtures:
        result |= _capabilities_from_wheels(fixture)
        channels = getattr(fixture, "fixture_channels", None)
        if not channels:
            continue
        for channel in channels:
            template = getattr(channel, "channel_template", None)
            if template is None:
                logger.debug("Channel %r has no template; skipping.", getattr(channel, "name", "?"))
                continue
            try:
                capabilities = template.get_capabilities()
            except AttributeError:
                logger.debug("Channel %r template has no get_capabilities(); skipping.", channel.name)
                continue
            for capability in capabilities:
                mapped = _tag_for(capability.type, channel.name)
                if mapped is not None:
                    result.add(mapped)
    return result


def gobo_wheels_of(fixture: UsedFixture) -> list[tuple[str, Wheel]]:
    """Return ``(wheel_name, wheel)`` tuples for wheels that contain gobo slots."""
    out: list[tuple[str, Wheel]] = []
    for name, wheel in _wheels_of(fixture).items():
        for slot in getattr(wheel, "slots", []):
            if slot.type in _GOBO_SLOT_TYPES:
                out.append((name, wheel))
                break
    return out


_BEAM_SUB_CAPABILITY_BY_TYPE: dict[CapabilityType, str] = {
    CapabilityType.ZOOM: "zoom",
    CapabilityType.BEAM_ANGLE: "zoom",
    CapabilityType.IRIS: "iris",
    CapabilityType.IRIS_EFFECT: "iris",
    CapabilityType.PRISM: "prism",
    CapabilityType.PRISM_ROTATION: "prism",
}


def beam_sub_capabilities(fixture: UsedFixture) -> set[str]:
    """Return the beam sub-capabilities (``"zoom"``, ``"iris"``, ``"prism"``) a fixture has.

    Walks the OFL channel templates to produce the finer-grained zoom/iris/
    prism split so a wash fixture with only ``ZOOM`` doesn't produce iris or
    prism output channels downstream.
    """
    found: set[str] = set()
    channels = getattr(fixture, "fixture_channels", None)
    if not channels:
        return found
    for channel in channels:
        template = getattr(channel, "channel_template", None)
        if template is None:
            continue
        try:
            capabilities = template.get_capabilities()
        except AttributeError:
            continue
        for capability in capabilities:
            sub = _BEAM_SUB_CAPABILITY_BY_TYPE.get(capability.type)
            if sub is not None:
                found.add(sub)
    return found
