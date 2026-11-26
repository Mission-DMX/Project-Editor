"""Single source of truth for how capabilities map to raw and exposed channels.

The property-based cue vfilter has three consumers that each used to carry
their own copy of the raw-channel / exposed-port names:

* :mod:`compiler` -- maps a raw channel to its logical capability.
* :mod:`_channel_ordering` -- knows which raw channels to hide and which
  synthesised outputs to add.
* :mod:`postprocess.factory` -- builds the filter graph that consumes the
  raw channels and produces the exposed ones.

Keeping those names in one place avoids subtle drift when, e.g., a new
sub-channel is added to a property.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.filter import DataType


# Raw channels used by the position property + its postprocess chain.
POSITION_VALUE_SUFFIX = "_value"
POSITION_CURVESEL_SUFFIX = "_curvesel"
PAN_VALUE = f"pan{POSITION_VALUE_SUFFIX}"
PAN_CURVESEL = f"pan{POSITION_CURVESEL_SUFFIX}"
TILT_VALUE = f"tilt{POSITION_VALUE_SUFFIX}"
TILT_CURVESEL = f"tilt{POSITION_CURVESEL_SUFFIX}"
PAN_EXPOSED = "pan"
TILT_EXPOSED = "tilt"

# Raw channels used by the dimmer property + the strobe-generator chain.
# ``BRIGHTNESS_RAW`` feeds the strobe generator from the native cue filter;
# the strobe generator then publishes the user-facing ``BRIGHTNESS`` port.
# Keeping the raw and exposed names distinct is essential: if both were
# ``"brightness"``, ``filter_serialization.py``'s override dictionary would
# rewrite the strobe filter's own brightness input to point at the strobe
# filter's value output, producing a self-link that stalls fish scheduling.
# Pan/tilt follow the same split (``pan_value`` raw, ``pan`` exposed).
BRIGHTNESS = "brightness"
BRIGHTNESS_RAW = "brightness_raw"
STROBEFREQ = "strobefreq"
DUTY_CYCLE = "duty_cycle"


@dataclass(slots=True, frozen=True)
class ExposedOutput:
    """A post-processed output surfaced on the vfilter's node."""

    name: str
    data_type_attr: str  # name of attribute on model.filter.DataType

    def data_type(self) -> DataType:
        """Resolve the referenced ``model.filter.DataType`` member."""
        from model.filter import DataType

        return getattr(DataType, self.data_type_attr)


# Raw channel local name -> capability key. ``_infer_capability`` iterates
# this map in order and uses ``startswith`` for prefix matching so dynamic
# names like ``goboslot_0`` / ``goborotation_1`` resolve correctly.
RAW_TO_CAPABILITY: dict[str, str] = {
    "pan": "pan",
    "tilt": "tilt",
    # ``brightness_raw`` is matched before ``brightness`` so the raw-channel
    # lookup never mistakes the exposed name for a raw one; ``startswith``
    # covers both via the ``BRIGHTNESS`` entry below.
    BRIGHTNESS_RAW: "dimmer",
    BRIGHTNESS: "dimmer",
    STROBEFREQ: "dimmer",
    DUTY_CYCLE: "dimmer",
    "color": "color",
    "focus": "focus",
    "zoom": "beam",
    "iris": "beam",
    "prism_selection": "beam",
    "prism_rotation": "beam",
    "goboslot": "gobo",
    "goborotation": "gobo",
    "frost_intensity": "frost",
}


# Raw channels that only exist to drive post-processing filters; the vfilter
# hides them on the node and exposes the result of the chain instead.
INTERNAL_LOCAL_NAMES: frozenset[str] = frozenset({
    BRIGHTNESS_RAW, STROBEFREQ, DUTY_CYCLE,
    PAN_VALUE, PAN_CURVESEL,
    TILT_VALUE, TILT_CURVESEL,
})


# Raw channel -> ``ExposedOutput`` for cases where the post-processed port has
# a different name/type than the raw channel. The dimmer entry mirrors the
# pan/tilt split: the native cue filter emits ``brightness_raw`` (hidden),
# the strobe generator exposes ``brightness`` as the user-facing port.
SYNTHESIZED_OUTPUTS: dict[str, ExposedOutput] = {
    PAN_VALUE: ExposedOutput(PAN_EXPOSED, "DT_16_BIT"),
    TILT_VALUE: ExposedOutput(TILT_EXPOSED, "DT_16_BIT"),
    BRIGHTNESS_RAW: ExposedOutput(BRIGHTNESS, "DT_DOUBLE"),
}
