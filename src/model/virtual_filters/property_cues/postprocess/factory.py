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

if TYPE_CHECKING:
    from model import Scene

logger = getLogger(__name__)

PositionTuple = tuple[int, int] | tuple[float, float] | None


@dataclass(slots=True)
class CapabilityContext:
    """Everything a strategy needs to build its chain for ONE instance."""

    scene: Scene
    cue_filter_id: str
    channel_name_prefix: str
    pan_range: tuple[int, int] | None = None
    tilt_range: tuple[int, int] | None = None
    pos: PositionTuple = None
    extra_params: dict[str, str] = field(default_factory=dict)


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

    value_src = f"{cue_fid}:{prefix}__{capability}_value"
    curvesel_src = f"{cue_fid}:{prefix}__{capability}_curvesel"

    sin_id = f"{base_id}_sin"
    cos_id = f"{base_id}_cos"
    switch_id = f"{base_id}_switch"
    range_id = f"{base_id}_range"

    sin_filter = Filter(ctx.scene, sin_id,
                        filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN, pos=ctx.pos)
    sin_filter.channel_links["value_in"] = value_src

    cos_filter = Filter(ctx.scene, cos_id,
                        filter_type=FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN, pos=ctx.pos)
    cos_filter.channel_links["value_in"] = value_src

    switch_filter = Filter(ctx.scene, switch_id,
                           filter_type=FilterTypeEnumeration.FILTER_SWITCH_FLOAT, pos=ctx.pos,
                           filter_configurations={"nr_inputs": "3"})
    switch_filter.channel_links["select"] = curvesel_src
    switch_filter.channel_links["0"] = value_src
    switch_filter.channel_links["1"] = f"{sin_id}:value"
    switch_filter.channel_links["2"] = f"{cos_id}:value"

    low, high = raw_range if raw_range is not None else _DEFAULT_16BIT_RANGE
    range_filter = Filter(
        ctx.scene, range_id,
        filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE,
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
        filters=(sin_filter, cos_filter, switch_filter, range_filter),
        external_ports={capability: (range_id, "value")},
    )


def _pan_strategy(ctx: CapabilityContext) -> PostprocessOutput:
    """Materialise the pan chain for a single fixture."""
    return _position_chain("pan", ctx.pan_range, ctx)


def _tilt_strategy(ctx: CapabilityContext) -> PostprocessOutput:
    """Materialise the tilt chain for a single fixture."""
    return _position_chain("tilt", ctx.tilt_range, ctx)


def _strobe_strategy(ctx: CapabilityContext) -> PostprocessOutput:
    """Placeholder for the future strobe generator.

    Warns once per call and falls back to the plain passthrough so unit tests and
    downstream fixtures still see a usable external port while the real generator
    is being developed.
    """
    logger.warning("strobe generator not yet available; passthrough")
    return _passthrough("strobe", ctx)


register_strategy("pan", _pan_strategy)
register_strategy("tilt", _tilt_strategy)
register_strategy("strobe", _strobe_strategy)
