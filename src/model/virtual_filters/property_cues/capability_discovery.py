"""Model-layer helpers to classify fixture capabilities for the property-cue vfilter.

Reads the fixture channel types and the OFL wheel slot types and maps them
to the vfilter's :class:`EnabledCapability` enum. Keeps the mapping
conservative: for anything that cannot be categorised unambiguously a
``DEBUG`` message is logged and the capability is skipped rather than
guessed.

Lives in the model layer so the vfilter / compiler can inspect fixtures
without pulling view-side code; the editor UI still re-uses these helpers
by importing them from here.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from model.ofl.ofl_fixture import CapabilityType, WheelSlotType
from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model.ofl.fixture import UsedFixture
    from model.ofl.ofl_fixture import Wheel

logger = getLogger(__name__)


_CAPABILITY_TYPE_TO_ENABLED: dict[CapabilityType, EnabledCapability] = {
    CapabilityType.COLOR_INTENSITY: EnabledCapability.COLOUR,
    CapabilityType.COLOR_PRESET: EnabledCapability.COLOUR,
    CapabilityType.COLOR_TEMPERATURE: EnabledCapability.COLOUR,
    CapabilityType.PAN: EnabledCapability.POSITION,
    CapabilityType.PAN_CONTINUOUS: EnabledCapability.POSITION,
    CapabilityType.TILT: EnabledCapability.POSITION,
    CapabilityType.TILT_CONTINUOUS: EnabledCapability.POSITION,
    CapabilityType.INTENSITY: EnabledCapability.DIMMER,
    CapabilityType.FOCUS: EnabledCapability.FOCUS,
    CapabilityType.ZOOM: EnabledCapability.BEAM,
    CapabilityType.IRIS: EnabledCapability.BEAM,
    CapabilityType.IRIS_EFFECT: EnabledCapability.BEAM,
    CapabilityType.PRISM: EnabledCapability.BEAM,
    CapabilityType.PRISM_ROTATION: EnabledCapability.BEAM,
    CapabilityType.BEAM_ANGLE: EnabledCapability.BEAM,
    CapabilityType.FROST: EnabledCapability.FROST,
    CapabilityType.FROST_EFFECT: EnabledCapability.FROST,
}


_GOBO_SLOT_TYPES = frozenset(
    {WheelSlotType.GOBO, WheelSlotType.ANIMATED_GOBO_START, WheelSlotType.ANIMATED_GOBO_END},
)


def _wheels_of(fixture: UsedFixture) -> dict[str, Wheel]:
    """Return the fixture's OFL wheel map (private access to the OFL template)."""
    ofl = getattr(fixture, "_fixture", None)
    return getattr(ofl, "wheels", {}) if ofl is not None else {}


def _capabilities_from_wheels(fixture: UsedFixture) -> set[EnabledCapability]:
    """Inspect wheel slot types directly: GOBO slots → GOBO; COLOR slots → COLOUR."""
    caps: set[EnabledCapability] = set()
    for wheel in _wheels_of(fixture).values():
        for slot in getattr(wheel, "slots", []):
            if slot.type in _GOBO_SLOT_TYPES:
                caps.add(EnabledCapability.GOBO)
            elif slot.type is WheelSlotType.COLOR:
                caps.add(EnabledCapability.COLOUR)
    return caps


def _capability_for(cap_type: CapabilityType, channel_name: str) -> EnabledCapability | None:
    """Return the EnabledCapability for a single non-wheel OFL capability, or None if unknown."""
    if cap_type == CapabilityType.WHEEL_SLOT:
        return None  # Handled via wheel-slot-type inspection in _capabilities_from_wheels.
    mapped = _CAPABILITY_TYPE_TO_ENABLED.get(cap_type)
    if mapped is None:
        logger.debug(
            "Capability type %s on channel %r has no EnabledCapability mapping; skipping.",
            cap_type,
            channel_name,
        )
    return mapped


def discover_capabilities(fixtures: Iterable[UsedFixture]) -> set[EnabledCapability]:
    """Union per-fixture capabilities derived from channel templates and wheel slot types."""
    result: set[EnabledCapability] = set()
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
                mapped = _capability_for(capability.type, channel.name)
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

    Used by the compiler to decide which of :class:`BeamProperty`'s channels
    should be exposed on this specific fixture. Walking the OFL channel
    templates mirrors :func:`discover_capabilities` but keeps the finer-
    grained zoom/iris/prism split so a wash fixture with only ``ZOOM``
    doesn't produce iris or prism output channels.
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
