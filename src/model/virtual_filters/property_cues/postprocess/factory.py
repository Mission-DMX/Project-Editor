"""Factory for post-processing filter chains per fixture capability.

Register additional strategies via :func:`register_strategy` -- the file-level docstring
is the public contract. The property-based cue vfilter calls
:func:`build_postprocess_chain` once per fixture-capability pair at show-file
elaboration time.

A *strategy* is a callable that takes a :class:`CapabilityContext` and returns a
:class:`PostprocessOutput` describing the native filters that should be appended to
the vfilter's instantiated filter list plus the ``(filter_id, port_name)`` the
vfilter should hand back from :meth:`resolve_output_port_id` for the capability.

If no strategy is registered for a given capability, :func:`build_postprocess_chain`
falls back to a passthrough that adds no filters and exposes the cue filter's
own output channel ``f"{channel_name_prefix}__{capability}"`` directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING

from model.filter import Filter, FilterTypeEnumeration
from model.filters.factory import construct_filter_instance
from model.virtual_filters.property_cues.capability_wiring import (
    BRIGHTNESS,
    BRIGHTNESS_RAW,
    DUTY_CYCLE,
    POSITION_CURVESEL_SUFFIX,
    POSITION_VALUE_SUFFIX,
    STROBEFREQ,
)

if TYPE_CHECKING:
    from model import Scene

logger = getLogger(__name__)

PositionTuple = tuple[int, int] | tuple[float, float] | None


@dataclass(slots=True)
class CapabilityContext:
    """Everything a strategy needs to build its chain for ONE instance.

    ``constant_inputs`` maps local raw-channel names (e.g. ``"brightness_raw"``)
    to the string value that will be emitted on the native cue filter for
    that channel. The compiler only populates an entry when the channel is
    DEFAULTED across every cue -- i.e. no cue dialed a keyframe for it --
    so a strategy can tell whether its input is "definitely this static
    value for the life of the show" or "a live stream coming from the cue
    filter". Strategies may use this to fold their whole chain down to a
    single constant filter (see the dimmer strategy for the pattern).
    """

    scene: Scene
    cue_filter_id: str
    channel_name_prefix: str
    pan_range: tuple[int, int] | None = None
    tilt_range: tuple[int, int] | None = None
    pos: PositionTuple = None
    extra_params: dict[str, str] = field(default_factory=dict)
    constant_inputs: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class PostprocessOutput:
    """What a strategy returns.

    ``filters`` are appended to the vfilter's instantiated filter list.
    ``external_ports`` maps the user-facing capability name (e.g. ``"pan"``) to the
    ``(filter_id, port_name)`` tuple that :meth:`resolve_output_port_id` should
    return for that capability. For a passthrough result the port tuple references
    the upstream cue filter directly.
    """

    filters: tuple[Filter, ...]
    external_ports: dict[str, tuple[str, str]]


PostprocessStrategy = Callable[[CapabilityContext], PostprocessOutput]


_STRATEGIES: dict[str, PostprocessStrategy] = {}


def register_strategy(capability: str, strategy: PostprocessStrategy) -> None:
    """Register a factory for ``capability``. Overrides any previous registration."""
    _STRATEGIES[capability] = strategy


def _passthrough(capability: str, ctx: CapabilityContext) -> PostprocessOutput:
    """Return the direct cue-filter output for ``capability`` with no extra filters."""
    port = (ctx.cue_filter_id, f"{ctx.channel_name_prefix}__{capability}")
    return PostprocessOutput(filters=(), external_ports={capability: port})


def build_postprocess_chain(capability: str, ctx: CapabilityContext) -> PostprocessOutput:
    """Dispatch to the registered strategy; fall back to passthrough if none registered.

    Passthrough treats the capability as a bare cue-filter output: no filters added,
    external_ports maps ``capability -> (ctx.cue_filter_id, f"{ctx.channel_name_prefix}__{capability}")``.
    """
    strategy = _STRATEGIES.get(capability)
    if strategy is None:
        return _passthrough(capability, ctx)
    return strategy(ctx)


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------

# Default (16-bit, full range) output range for the float->16bit adapter when a
# fixture does not specify a physical range in :class:`CapabilityContext`.
_DEFAULT_16BIT_RANGE: tuple[int, int] = (0, 65535)


def _position_chain(capability: str, raw_range: tuple[int, int] | None,
                    ctx: CapabilityContext) -> PostprocessOutput:
    """Build the ``value / curvesel`` trig+switch+range chain shared by pan and tilt.

    Layout (``*`` denotes filters this strategy creates):

    ``cue_filter`` --+--> ``*_sin`` (sin) ------+
                     +--> ``*_cos`` (cos) ------+--> ``*_switch`` --> ``*_range`` --> external
                     +---------------------------+                        ^
    curvesel --------------------------------------------------------- select
    """
    prefix = ctx.channel_name_prefix
    cue_fid = ctx.cue_filter_id
    base_id = f"{cue_fid}__{prefix}__{capability}"

    value_src = f"{cue_fid}:{prefix}__{capability}{POSITION_VALUE_SUFFIX}"
    curvesel_src = f"{cue_fid}:{prefix}__{capability}{POSITION_CURVESEL_SUFFIX}"

    sin_id = f"{base_id}_sin"
    cos_id = f"{base_id}_cos"
    switch_id = f"{base_id}_switch"
    range_id = f"{base_id}_range"

    # ``construct_filter_instance`` returns the registered Filter subclass
    # when one exists; that subclass's ``_rebuild_io`` populates ``in_data_types``
    # and ``default_values`` so fish's serialiser can wire default nodes for
    # every input the filter declares (trig filters in particular take a
    # ``factor_outer`` / ``factor_inner`` / ``phase`` / ``offset`` quartet
    # that fish will otherwise reject at configure time).
    sin_filter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN), sin_id, pos=ctx.pos,
    )
    sin_filter.channel_links["value_in"] = value_src

    cos_filter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN), cos_id, pos=ctx.pos,
    )
    cos_filter.channel_links["value_in"] = value_src

    # L23: sin/cos trig filters emit floats in [-1.0, 1.0]. Feeding them
    # into the final [0, 1]-input range adapter would clamp the entire
    # negative half of the waveform onto the low bound, so a cos pan curve
    # only ever reached the positive half of the fixture's mechanical
    # travel. Remap each trig output into [0.0, 1.0] here so the switch's
    # three inputs share a common range and the direct branch (which
    # already carries values in [0, 1]) still maps correctly through the
    # main range adapter.
    sin_rescale_id = f"{base_id}_sin_to_01"
    cos_rescale_id = f"{base_id}_cos_to_01"
    sin_rescale = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE),
        sin_rescale_id, pos=ctx.pos,
        filter_configurations={
            "lower_bound_in": "-1.0", "upper_bound_in": "1.0",
            "lower_bound_out": "0.0", "upper_bound_out": "1.0",
            "limit_range": "1",
        },
    )
    sin_rescale.channel_links["value_in"] = f"{sin_id}:value"
    cos_rescale = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE),
        cos_rescale_id, pos=ctx.pos,
        filter_configurations={
            "lower_bound_in": "-1.0", "upper_bound_in": "1.0",
            "lower_bound_out": "0.0", "upper_bound_out": "1.0",
            "limit_range": "1",
        },
    )
    cos_rescale.channel_links["value_in"] = f"{cos_id}:value"

    switch_filter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_SWITCH_FLOAT), switch_id, pos=ctx.pos,
        filter_configurations={"nr_inputs": "3"},
    )
    switch_filter.channel_links["select"] = curvesel_src
    switch_filter.channel_links["0"] = value_src
    switch_filter.channel_links["1"] = f"{sin_rescale_id}:value"
    switch_filter.channel_links["2"] = f"{cos_rescale_id}:value"

    low, high = raw_range if raw_range is not None else _DEFAULT_16BIT_RANGE
    range_filter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE), range_id,
        pos=ctx.pos,
        filter_configurations={
            "lower_bound_in": "0.0",
            "upper_bound_in": "1.0",
            "lower_bound_out": str(low),
            "upper_bound_out": str(high),
            "limit_range": "1",
        },
    )
    range_filter.channel_links["value_in"] = f"{switch_id}:out"

    return PostprocessOutput(
        filters=(sin_filter, cos_filter, sin_rescale, cos_rescale, switch_filter, range_filter),
        external_ports={capability: (range_id, "value")},
    )


def _pan_strategy(ctx: CapabilityContext) -> PostprocessOutput:
    """Materialise the pan chain for a single fixture."""
    return _position_chain("pan", ctx.pan_range, ctx)


def _tilt_strategy(ctx: CapabilityContext) -> PostprocessOutput:
    """Materialise the tilt chain for a single fixture."""
    return _position_chain("tilt", ctx.tilt_range, ctx)


_DEFAULT_SLOWEST_PERIOD_MS = "500.0"


def _try_fold_dimmer(ctx: CapabilityContext, base_id: str) -> PostprocessOutput | None:
    """If every raw dimmer input is a known constant and the strobe is OFF, emit a single float constant.

    The emitted constant is written to the ``brightness`` port.

    Returns ``None`` when the fold isn't safe; the caller then builds the
    full freq/duty/strobe chain. The strobe generator with
    ``frequency == 0`` is a bit-exact passthrough of brightness, which is
    why dropping the chain is semantically equivalent.
    """
    const_inputs = ctx.constant_inputs
    if not const_inputs:
        return None
    br = const_inputs.get(BRIGHTNESS_RAW)
    sf = const_inputs.get(STROBEFREQ)
    if br is None or sf is None:
        return None
    try:
        if float(sf) != 0.0:
            return None
    except (TypeError, ValueError):
        return None
    folded_id = f"{base_id}_folded"
    folded = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_CONSTANT_FLOAT), folded_id,
        pos=ctx.pos,
    )
    folded.initial_parameters["value"] = br
    return PostprocessOutput(
        filters=(folded,),
        external_ports={"brightness": (folded_id, "value")},
    )


def _dimmer_strategy(ctx: CapabilityContext) -> PostprocessOutput:
    """Gate the raw brightness through the float strobe generator.

    Pulls ``brightness_raw``, ``strobefreq`` and ``duty_cycle`` from the cue
    filter; converts the two float control inputs into 8-bit values with
    :class:`FILTER_ARITHMETICS_FLOAT_TO_8BIT`; routes everything into
    :class:`FILTER_SERIES_STROBE_GENERATOR_FLOAT`. The strobe generator's float
    ``value`` output is exposed as the fixture's ``brightness`` capability.

    The *raw* input name is ``brightness_raw`` (not ``brightness``) because
    this strategy publishes the external port named ``brightness``. If the
    raw and exposed names matched, the serialiser's channel-override
    dictionary (``filter_serialization.py::_create_filter_element_for_fish``)
    would rewrite the strobe filter's own brightness input to point at its
    own value output, creating a self-link that fish's scheduler rejects.
    Pan/tilt follow the same split.

    When every raw input is known to be a constant (``ctx.constant_inputs``
    carries a value for all three) **and** the constant strobe frequency
    is zero, the strategy folds the whole chain down to a single
    ``FILTER_CONSTANT_FLOAT`` exposed as ``brightness``. The strobe
    generator with ``frequency == 0`` is a bit-exact passthrough of its
    brightness input, so this is correct: no freq adapter, no duty
    adapter, no strobe filter.
    """
    prefix = ctx.channel_name_prefix
    cue_fid = ctx.cue_filter_id
    base_id = f"{cue_fid}__{prefix}__dimmer"

    folded = _try_fold_dimmer(ctx, base_id)
    if folded is not None:
        return folded

    brightness_src = f"{cue_fid}:{prefix}__{BRIGHTNESS_RAW}"
    strobefreq_src = f"{cue_fid}:{prefix}__{STROBEFREQ}"
    duty_src = f"{cue_fid}:{prefix}__{DUTY_CYCLE}"

    freq8bit_id = f"{base_id}_freq8bit"
    duty8bit_id = f"{base_id}_duty8bit"
    strobe_id = f"{base_id}_strobe"

    # Use the factory so each native filter picks up the registered
    # subclass's I/O signature + default values; otherwise fish rejects
    # the serialised show at configure time with "channel mapping does
    # not contain channel X of type Y".
    freq_adapter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT), freq8bit_id,
        pos=ctx.pos,
    )
    freq_adapter.channel_links["value_in"] = strobefreq_src

    duty_adapter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT), duty8bit_id,
        pos=ctx.pos,
    )
    duty_adapter.channel_links["value_in"] = duty_src

    strobe_filter = construct_filter_instance(
        ctx.scene, int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT), strobe_id,
        pos=ctx.pos,
        filter_configurations={"slowest_period_ms": _DEFAULT_SLOWEST_PERIOD_MS},
    )
    strobe_filter.channel_links["brightness"] = brightness_src
    strobe_filter.channel_links["frequency"] = f"{freq8bit_id}:value"
    strobe_filter.channel_links["duty_cycle"] = f"{duty8bit_id}:value"

    return PostprocessOutput(
        filters=(freq_adapter, duty_adapter, strobe_filter),
        external_ports={"brightness": (strobe_id, "value")},
    )


register_strategy("pan", _pan_strategy)
register_strategy("tilt", _tilt_strategy)
register_strategy("dimmer", _dimmer_strategy)
