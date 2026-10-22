"""Resolve which EnabledCapability values are available for a selection.

Reads the fixture channel types and maps them via the
``capability_type_to_enabled_capability`` table into the vfilter's
user-facing capability enum. Keeps the mapping conservative: for
anything that cannot be categorised unambiguously, a ``DEBUG`` message
is logged and the capability is skipped rather than guessed.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from model.ofl.ofl_fixture import CapabilityType
from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model.ofl.fixture import UsedFixture

logger = getLogger(__name__)


# Direct 1:1 mappings from OFL CapabilityType to the vfilter's EnabledCapability.
# PAN/TILT are both reported as POSITION; WHEEL_SLOT is treated as GOBO when the
# wheel is not a dedicated colour wheel (see _resolve_wheel_slot below).
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


def _resolve_wheel_slot(channel_name: str) -> EnabledCapability | None:
    """A WHEEL_SLOT capability maps to COLOUR for colour wheels, GOBO otherwise."""
    lowered = channel_name.lower()
    if "color" in lowered or "colour" in lowered:
        return EnabledCapability.COLOUR
    return EnabledCapability.GOBO


def _capability_for(cap_type: CapabilityType, channel_name: str) -> EnabledCapability | None:
    """Return the EnabledCapability for a single OFL capability, or None if unknown."""
    if cap_type == CapabilityType.WHEEL_SLOT:
        return _resolve_wheel_slot(channel_name)
    mapped = _CAPABILITY_TYPE_TO_ENABLED.get(cap_type)
    if mapped is None:
        logger.debug(
            "Capability type %s on channel %r has no EnabledCapability mapping; skipping.",
            cap_type,
            channel_name,
        )
    return mapped


def discover_capabilities(fixtures: Iterable[UsedFixture]) -> set[EnabledCapability]:
    """Walk every channel template of each fixture and union the mapped capabilities.

    Fixtures whose channels have no template or no capabilities are skipped.
    DIMMER cannot be inferred from a template capability alone (no OFL type
    corresponds to a dedicated master dimmer that isn't INTENSITY), so this
    function treats INTENSITY as DIMMER consistently.
    """
    result: set[EnabledCapability] = set()
    for fixture in fixtures:
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
