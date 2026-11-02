"""Enumerate default channel specs for every (fixture, enabled capability) pair.

Even without any dialed-in assignment, the native cue filter has to expose
one channel per capability so downstream filters can hook up.  Lives in its
own module so :mod:`compiler` stays below its 300-LOC budget.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.properties import (
    BeamProperty,
    ColourProperty,
    DimmerProperty,
    FocusProperty,
    FrostProperty,
    GoboProperty,
    PositionProperty,
    Property,
)

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.model.fixture_selection import FixtureSelection

ResolvedChild = tuple[str, int | None]
NameResolver = Callable[[str], str]
CapabilityLookup = Callable[[str], set[str]]
GoboWheelCountLookup = Callable[[str], int]
BeamSubCapabilityLookup = Callable[[str], set[str]]

_PROPERTY_CLASS: dict[str, type[Property]] = {
    "dimmer": DimmerProperty, "position": PositionProperty,
    "colour": ColourProperty, "color": ColourProperty,
    "beam": BeamProperty, "gobo": GoboProperty,
    "focus": FocusProperty, "frost": FrostProperty,
}


def property_kwargs_for_fixture(
    property_id: str, fixture_id: str,
    gobo_wheel_count_lookup: GoboWheelCountLookup | None,
    beam_sub_capabilities_lookup: BeamSubCapabilityLookup | None,
) -> dict[str, object]:
    """Return constructor kwargs that shape the property to the fixture's physical caps.

    Used by both the default-spec enumeration and the per-assignment spec
    lookup so that whether or not the user has dialed in a value, the
    emitted channel set matches what the fixture actually supports.
    """
    kwargs: dict[str, object] = {}
    if property_id == "gobo" and gobo_wheel_count_lookup is not None:
        wheel_count = gobo_wheel_count_lookup(fixture_id)
        if wheel_count > 0:
            kwargs["wheel_count"] = wheel_count
    if property_id == "beam" and beam_sub_capabilities_lookup is not None:
        subs = beam_sub_capabilities_lookup(fixture_id)
        kwargs["include_zoom"] = "zoom" in subs
        kwargs["include_iris"] = "iris" in subs
        kwargs["include_prism"] = "prism" in subs
    return kwargs


def default_specs_for_fixtures(
    selection: FixtureSelection,
    children: list[ResolvedChild],
    prefix_for: Callable[[str, int | None], str],
    capability_lookup: CapabilityLookup | None,
    gobo_wheel_count_lookup: GoboWheelCountLookup | None,
    beam_sub_capabilities_lookup: BeamSubCapabilityLookup | None = None,
) -> dict[str, ChannelSpec]:
    """Return default channel specs for every (fixture, enabled capability) pair.

    ``capability_lookup`` optionally restricts expansion to the capabilities a
    fixture actually supports; without it we materialise channels for every
    enabled capability (headless-test friendly). ``gobo_wheel_count_lookup``
    yields the per-fixture gobo wheel count so moving spots with two gobo
    wheels get both channel pairs. ``beam_sub_capabilities_lookup`` reports
    the subset of beam sub-capabilities (``"zoom"``, ``"iris"``, ``"prism"``)
    a fixture actually supports so wash fixtures with only ``ZOOM`` get just
    the zoom channel and no spurious iris / prism channels.
    """
    specs: dict[str, ChannelSpec] = {}
    enabled = {cap.value for cap in selection.enabled_capabilities}
    for fid, segment in children:
        prefix = prefix_for(fid, segment)
        supported = capability_lookup(fid) if capability_lookup is not None else enabled
        for property_id in enabled & supported:
            cls = _PROPERTY_CLASS.get(property_id)
            if cls is None:
                continue
            kwargs = property_kwargs_for_fixture(
                property_id, fid, gobo_wheel_count_lookup, beam_sub_capabilities_lookup,
            )
            try:
                prop = cls(**kwargs)  # type: ignore[arg-type]
            except TypeError:
                continue
            for s in prop.channel_specs:
                channel_name = f"{prefix}__{s.name}"
                specs.setdefault(channel_name, ChannelSpec(
                    name=channel_name, data_type=s.data_type,
                    default_value=s.default_value, aliases=s.aliases,
                ))
    return specs
