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
BRIGHTNESS = "brightness"
STROBEFREQ = "strobefreq"
DUTY_CYCLE = "duty_cycle"


@dataclass(slots=True, frozen=True)
class ExposedOutput:
    """A post-processed output surfaced on the vfilter's node."""

    name: str
    data_type_attr: str  # name of attribute on model.filter.DataType

    def data_type(self) -> DataType:
        from model.filter import DataType

        return getattr(DataType, self.data_type_attr)


# Raw channel local name -> capability key. ``_infer_capability`` iterates
# this map in order and uses ``startswith`` for prefix matching so dynamic
# names like ``goboslot_0`` / ``goborotation_1`` resolve correctly.
RAW_TO_CAPABILITY: dict[str, str] = {
    "pan": "pan",
    "tilt": "tilt",
    BRIGHTNESS: "dimmer",
    STROBEFREQ: "dimmer",
    DUTY_CYCLE: "dimmer",
    "color": "colour",
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
    STROBEFREQ, DUTY_CYCLE,
    PAN_VALUE, PAN_CURVESEL,
    TILT_VALUE, TILT_CURVESEL,
})


# Raw channel -> ``ExposedOutput`` for cases where the post-processed port has
# a different name/type than the raw channel. ``brightness`` isn't in here
# because the strobe generator preserves the float type and reuses the name
# (``resolve_output_port_id`` re-routes it to the generator's output).
SYNTHESIZED_OUTPUTS: dict[str, ExposedOutput] = {
    PAN_VALUE: ExposedOutput(PAN_EXPOSED, "DT_16_BIT"),
    TILT_VALUE: ExposedOutput(TILT_EXPOSED, "DT_16_BIT"),
}
