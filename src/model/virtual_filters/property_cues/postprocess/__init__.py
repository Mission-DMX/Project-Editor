"""Post-processing filter chain factories for the property-based cue vfilter.

Each registered strategy maps a *capability* name (``"pan"``, ``"tilt"``,
``"strobe"``, ...) to a factory that materialises the native filters required to
turn the raw cue filter outputs into the user-facing property value, and reports
back which external port the vfilter should expose for that capability.
"""

from __future__ import annotations

from model.virtual_filters.property_cues.postprocess.factory import (
    CapabilityContext,
    PostprocessOutput,
    PostprocessStrategy,
    build_postprocess_chain,
    register_strategy,
)

__all__ = [
    "CapabilityContext",
    "PostprocessOutput",
    "PostprocessStrategy",
    "build_postprocess_chain",
    "register_strategy",
]
