"""Enumerate default channel specs for every (fixture, enabled capability) pair.

Even without any dialed-in assignment, the native cue filter has to expose
one channel per capability so downstream filters can hook up.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.virtual_filters.property_cues.channel_spec import ChannelSpec

if TYPE_CHECKING:
    from collections.abc import Callable

    from model.virtual_filters.property_cues.compiler import (
        BeamSubCapabilityLookup,
        CapabilityLookup,
        ColorSegmentCountLookup,
        GoboWheelCountLookup,
        ResolvedChild,
    )
    from model.virtual_filters.property_cues.model.fixture_selection import FixtureSelection

__all__ = [
    "default_specs_for_fixtures",
    "property_kwargs_for_fixture",
]


def property_kwargs_for_fixture(
    property_id: str, fixture_id: str,
    gobo_wheel_count_lookup: GoboWheelCountLookup | None,
    beam_sub_capabilities_lookup: BeamSubCapabilityLookup | None,
    color_segment_count_lookup: ColorSegmentCountLookup | None = None,
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
    if property_id == "color" and color_segment_count_lookup is not None:
        segment_count = color_segment_count_lookup(fixture_id)
        if segment_count > 0:
            kwargs["segment_count"] = segment_count
    return kwargs


def default_specs_for_fixtures(
    selection: FixtureSelection,
    children: list[ResolvedChild],
    prefix_for: Callable[[str, int | None], str],
    capability_lookup: CapabilityLookup | None,
    gobo_wheel_count_lookup: GoboWheelCountLookup | None,
    beam_sub_capabilities_lookup: BeamSubCapabilityLookup | None = None,
    color_segment_count_lookup: ColorSegmentCountLookup | None = None,
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
    ``color_segment_count_lookup`` returns the number of independent HSI
    colour segments on the fixture, so multi-pixel LED bars expose one
    ``color_N`` output per segment.
    """
    # Local import to break the ``compiler.py <-> _default_specs.py`` import
    # cycle: ``compiler.py`` owns ``_PROPERTY_CLASS`` (the single source of
    # truth) and imports ``default_specs_for_fixtures`` from here at module
    # scope, so importing back is only safe at call time.
    from model.virtual_filters.property_cues.capability_wiring import INTERNAL_LOCAL_NAMES
    from model.virtual_filters.property_cues.compiler import _PROPERTY_CLASS
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
                property_id, fid,
                gobo_wheel_count_lookup, beam_sub_capabilities_lookup,
                color_segment_count_lookup,
            )
            try:
                prop = cls(**kwargs)  # type: ignore[arg-type]
            except TypeError:
                continue
            for s in prop.channel_specs:
                channel_name = f"{prefix}__{s.name}"
                specs.setdefault(channel_name, ChannelSpec(
                    name=channel_name, data_type=s.data_type,
                    default_value=s.default_value, discrete=s.discrete,
                    capability=property_id,
                    exposed_locally=s.name not in INTERNAL_LOCAL_NAMES,
                ))
    return specs
