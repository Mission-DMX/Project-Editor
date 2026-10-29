"""Concrete properties for the property-based cue vfilter (WP4)."""

from model.virtual_filters.property_cues.properties.base import (
    TIMESTEPS_PER_SECOND,
    Property,
    child_start_timestep,
    seconds_to_timesteps,
)
from model.virtual_filters.property_cues.properties.beam import BeamProperty
from model.virtual_filters.property_cues.properties.colour import ColourProperty
from model.virtual_filters.property_cues.properties.dimmer import DimmerProperty
from model.virtual_filters.property_cues.properties.focus import FocusProperty
from model.virtual_filters.property_cues.properties.frost import FrostProperty
from model.virtual_filters.property_cues.properties.gobo import GoboProperty
from model.virtual_filters.property_cues.properties.position import (
    CURVE_COS,
    CURVE_DIRECT,
    CURVE_SIN,
    PositionProperty,
)

__all__ = [
    "CURVE_COS",
    "CURVE_DIRECT",
    "CURVE_SIN",
    "TIMESTEPS_PER_SECOND",
    "BeamProperty",
    "ColourProperty",
    "DimmerProperty",
    "FocusProperty",
    "FrostProperty",
    "GoboProperty",
    "PositionProperty",
    "Property",
    "child_start_timestep",
    "seconds_to_timesteps",
]
