"""Single source of truth for the property-cue vfilter's property catalogue.

Before this module existed, nine different tables across the compile pipeline,
the editor widgets, the step tree and the preset editor each carried their own
copy of "which properties exist, what channels they emit, what label the UI
shows". They had already drifted by the time S1 was authored: the preset
editor listed the wrong dimmer channel, the step tree was missing a frost
column, and the capability-wiring map re-declared facts that lived on the
property subclasses anyway.

:data:`REGISTRY` is the authoritative list; the small accessor helpers
(:func:`properties_in_order`, :func:`property_class_for`, ...) give consumers
one import to reach for instead of maintaining their own tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
from model.virtual_filters.property_cues.properties import (
    BeamProperty,
    ColorProperty,
    DimmerProperty,
    FocusProperty,
    FrostProperty,
    GoboProperty,
    PositionProperty,
)

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.properties import Property


@dataclass(slots=True, frozen=True)
class PropertyEntry:
    """Everything the editor and compile pipeline need to know about one property.

    The order of fields here drives the order of tabs in the property pane,
    columns in the step tree, and groups in the output-channel sort key.
    Consumers that need a specific subset (preset editor channels, step tree
    column header, etc.) go through the ``*_for`` accessors so adding a new
    property only requires adding a :class:`PropertyEntry` here.
    """

    id: str
    """Stable identifier used everywhere as a dict key (e.g. ``"dimmer"``)."""

    label: str
    """Human-readable label for tabs, columns and the "Applies for" combo."""

    capability: EnabledCapability
    """The fixture-selection capability toggle that gates this property."""

    property_class: type[Property]
    """The :class:`Property` subclass the compiler instantiates."""

    preset_channels: tuple[str, ...]
    """Fixed local channel names the preset editor renders as table columns.

    For dynamic shapes (gobo wheel count, colour segment count) only a
    representative subset is listed; the compiler's dynamic specs still
    honour the fixture's physical shape.
    """

    step_tree_column: str | None
    """Column header for this property in the step tree, or ``None`` to hide."""

    within_property_channel_order: tuple[str, ...]
    """Deterministic ordering for raw channels within this property.

    Used by :mod:`_channel_ordering` to produce stable left-to-right output
    port ordering on the vfilter node.
    """


REGISTRY: tuple[PropertyEntry, ...] = (
    PropertyEntry(
        id="dimmer",
        label="Dimmer",
        capability=EnabledCapability.DIMMER,
        property_class=DimmerProperty,
        preset_channels=("brightness_raw", "strobefreq", "duty_cycle"),
        step_tree_column="Dimmer",
        within_property_channel_order=("brightness", "brightness_raw", "strobefreq", "duty_cycle"),
    ),
    PropertyEntry(
        id="position",
        label="Position",
        capability=EnabledCapability.POSITION,
        property_class=PositionProperty,
        preset_channels=("pan_value", "pan_curvesel", "tilt_value", "tilt_curvesel"),
        step_tree_column="Position",
        within_property_channel_order=(
            "pan", "pan_value", "pan_curvesel", "tilt", "tilt_value", "tilt_curvesel",
        ),
    ),
    PropertyEntry(
        id="color",
        label="Color",
        capability=EnabledCapability.COLOR,
        property_class=ColorProperty,
        preset_channels=("color",),
        step_tree_column="Color",
        within_property_channel_order=("color",),
    ),
    PropertyEntry(
        id="gobo",
        label="Gobo",
        capability=EnabledCapability.GOBO,
        property_class=GoboProperty,
        preset_channels=("goboslot_0", "goborotation_0", "goboslot_1", "goborotation_1"),
        step_tree_column="Gobo",
        within_property_channel_order=(),  # ordered dynamically by wheel index
    ),
    PropertyEntry(
        id="beam",
        label="Beam",
        capability=EnabledCapability.BEAM,
        property_class=BeamProperty,
        preset_channels=("zoom", "iris", "prism_selection", "prism_rotation"),
        step_tree_column="Beam",
        within_property_channel_order=("zoom", "prism_selection", "prism_rotation", "iris"),
    ),
    PropertyEntry(
        id="focus",
        label="Focus",
        capability=EnabledCapability.FOCUS,
        property_class=FocusProperty,
        preset_channels=("focus",),
        step_tree_column="Focus",
        within_property_channel_order=("focus",),
    ),
    PropertyEntry(
        id="frost",
        label="Frost",
        capability=EnabledCapability.FROST,
        property_class=FrostProperty,
        preset_channels=("frost_intensity",),
        step_tree_column="Frost",
        within_property_channel_order=("frost_intensity",),
    ),
)


_BY_ID: dict[str, PropertyEntry] = {entry.id: entry for entry in REGISTRY}


def properties_in_order() -> tuple[PropertyEntry, ...]:
    """Return all registered properties in display order."""
    return REGISTRY


def entry_for(property_id: str) -> PropertyEntry | None:
    """Return the :class:`PropertyEntry` for ``property_id`` or ``None`` if unknown."""
    return _BY_ID.get(property_id)


def property_class_for(property_id: str) -> type[Property] | None:
    """Return the :class:`Property` subclass registered under ``property_id``."""
    entry = _BY_ID.get(property_id)
    return entry.property_class if entry is not None else None


def property_class_map() -> dict[str, type[Property]]:
    """Return a fresh ``{property_id: Property subclass}`` dict for all entries."""
    return {entry.id: entry.property_class for entry in REGISTRY}


def preset_channels_for(property_id: str) -> tuple[str, ...]:
    """Return the fixed preset-editor channel list for ``property_id``."""
    entry = _BY_ID.get(property_id)
    return entry.preset_channels if entry is not None else ()
