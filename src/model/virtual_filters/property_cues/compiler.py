"""Translate a PropertyCueFilterModel into native cue filter + postprocess chain + port map."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING

from model.filter import DataType, Filter, FilterTypeEnumeration
from model.filter_data.transfer_function import TransferFunction
from model.filters.factory import construct_filter_instance
from model.virtual_filters.property_cues import capability_wiring as _capability_wiring
from model.virtual_filters.property_cues._default_specs import default_specs_for_fixtures
from model.virtual_filters.property_cues._native_builder import build_native
from model.virtual_filters.property_cues.channel_consolidator import consolidate
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.model.fixture_selection import FixtureSelection, SelectionEntryKind
from model.virtual_filters.property_cues.model.property_step import (
    ManualPropertyAssignment,
    PresetPropertyAssignment,
    PropertyAssignment,
)
from model.virtual_filters.property_cues.postprocess import (
    CapabilityContext,
    PostprocessOutput,
    build_postprocess_chain,
)
from model.virtual_filters.property_cues.presets import evaluate_preset, load_preset_library
from model.virtual_filters.property_cues.properties import (
    BeamProperty,
    ColorProperty,
    DimmerProperty,
    FocusProperty,
    FrostProperty,
    GoboProperty,
    PositionProperty,
    Property,
    color_channel_name,
)
from model.virtual_filters.property_cues.solver import KeyframeSolver, RequestGroup, SolveInput

if TYPE_CHECKING:
    from model import Scene
    from model.filter_data.cues.cue import KeyFrame
    from model.filter_data.cues.cue_filter_model import CueFilterModel
    from model.virtual_filters.property_cues.channel_consolidator import ConsolidationMap
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.model.property_cue import PropertyCue
    from model.virtual_filters.property_cues.presets import EffectPreset

logger = getLogger(__name__)

ResolvedChild = tuple[str, int | None]
FixtureResolver = Callable[[FixtureSelection], list[ResolvedChild]]
NameResolver = Callable[[str], str]
# Return the set of enabled-capability string values the fixture supports.
CapabilityLookup = Callable[[str], set[str]]
# Return the number of gobo wheels on the fixture (0 if none).
GoboWheelCountLookup = Callable[[str], int]
# Return the beam sub-capabilities ("zoom", "iris", "prism") a fixture has.
BeamSubCapabilityLookup = Callable[[str], set[str]]
# Return the number of independent HSI colour segments on the fixture (0 if none).
ColorSegmentCountLookup = Callable[[str], int]

_SANITISE = re.compile(r"[^A-Za-z0-9_]")
_PROPERTY_CLASS: dict[str, type[Property]] = {
    "dimmer": DimmerProperty, "position": PositionProperty,
    "color": ColorProperty,
    "beam": BeamProperty, "gobo": GoboProperty,
    "focus": FocusProperty, "frost": FrostProperty,
}
_CAPABILITY_FROM_LOCAL = _capability_wiring.RAW_TO_CAPABILITY
@dataclass(slots=True)
class CompileResult:
    """Outcome of compiling a property-cue vfilter into a native cue model and postprocess filters."""

    native_model: CueFilterModel
    postprocess_filters: tuple[Filter, ...]
    consolidation: ConsolidationMap
    external_ports: dict[str, tuple[str, str]]
    channel_specs: dict[str, ChannelSpec] = field(default_factory=dict)


def _default_resolver(selection: FixtureSelection) -> list[ResolvedChild]:
    return [(e.id, None) for e in selection.entries if e.kind is SelectionEntryKind.FIXTURE]


def _default_name_resolver(fixture_id: str) -> str:
    return fixture_id


def _prefix(fixture_id: str, segment: int | None, name_resolver: NameResolver) -> str:
    """Produce a sanitised, human-readable channel prefix for a fixture.

    ``name_resolver`` maps a raw fixture id (typically its UUID) to a stage
    name (e.g. ``"Hero Spot #3"``). The result is passed through
    :data:`_SANITISE` so stage names with spaces or punctuation produce a
    legal filter channel identifier.
    """
    base = _SANITISE.sub("_", name_resolver(fixture_id))
    return base if segment is None else f"{base}.segment{int(segment)}"


def _resolve_path_children(path: str, children: list[ResolvedChild]) -> list[tuple[int, ResolvedChild]]:
    fid: str | None = None
    seg: int | None = None
    for comp in (c for c in path.split("/") if c):
        if comp.startswith("fixture:"):
            fid = comp[len("fixture:"):]
        elif comp.startswith("segment:"):
            try:
                seg = int(comp[len("segment:"):])
            except ValueError:
                seg = None
    out = [(idx, child) for idx, child in enumerate(children)
           if (fid is None or child[0] == fid) and (seg is None or child[1] == seg)]
    if not out and fid is None:
        out = list(enumerate(children))
    return out


def _infer_capability(local: str) -> str:
    for token, cap in _CAPABILITY_FROM_LOCAL.items():
        if local.startswith(token):
            return cap
    return local


def _build_property(property_id: str, assignment: ManualPropertyAssignment,
                    fixture_kwargs: dict[str, object]) -> Property:
    cls = _PROPERTY_CLASS.get(property_id)
    if cls is None:
        raise ValueError(f"Unknown property type: {property_id!r}")
    try:
        transition = TransferFunction(assignment.transition)
    except ValueError:
        transition = TransferFunction.LINEAR
    kwargs = {**fixture_kwargs, **assignment.values, "transition": transition}
    try:
        return cls(**kwargs)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"Cannot build {property_id!r} from {assignment.values!r}: {exc}") from exc


def _spec_table_for(
    property_id: str, prefix: str, assignment: PropertyAssignment | None,
    fixture_kwargs: dict[str, object],
) -> dict[str, ChannelSpec]:
    """Return channel specs for ``property_id`` prefixed with ``prefix``.

    ``fixture_kwargs`` carries per-fixture shape (gobo wheel_count, beam
    include_* flags); manual assignments override with the user's values.
    """
    cls = _PROPERTY_CLASS.get(property_id)
    if cls is None:
        return {}
    try:
        if isinstance(assignment, ManualPropertyAssignment):
            kwargs = {**fixture_kwargs,
                      **{k: v for k, v in assignment.values.items() if k != "transition"}}
            prop = cls(**kwargs)  # type: ignore[arg-type]
        else:
            prop = cls(**fixture_kwargs)  # type: ignore[arg-type]
    except TypeError:
        return {}
    return {f"{prefix}__{s.name}": ChannelSpec(
        name=f"{prefix}__{s.name}", data_type=s.data_type,
        default_value=s.default_value, aliases=s.aliases,
    ) for s in prop.channel_specs}


def _emit_requests(
    assignment: PropertyAssignment, property_id: str, step_start: int, step_duration: int,
    child_index: int, library: dict[str, EffectPreset] | None,
    fixture_kwargs: dict[str, object],
) -> dict[str, list]:
    if isinstance(assignment, ManualPropertyAssignment):
        prop = _build_property(property_id, assignment, fixture_kwargs)
        return prop.generate_requests(
            step_start_40hz=step_start, step_duration_40hz=step_duration,
            child_index=child_index, distribution=assignment.distribution,
        )
    if isinstance(assignment, PresetPropertyAssignment):
        delay = assignment.distribution.delay_for_child(child_index)
        lib = library if library is not None else load_preset_library()
        preset = lib.get(assignment.preset_id)
        if preset is None:
            raise ValueError(f"Unknown preset id: {assignment.preset_id!r}")
        return evaluate_preset(preset, assignment.hint_values, step_start, step_duration, delay)
    raise ValueError(f"Unknown assignment type: {type(assignment).__name__}")


def _child_supports_property(fixture_id: str, property_id: str,
                             capability_lookup: CapabilityLookup | None) -> bool:
    """Return True when ``fixture_id`` physically supports ``property_id``.

    Without a ``capability_lookup`` (headless tests, no board attached) the
    assignment is let through so unit tests that stub out the lookup still
    see channels materialise.
    """
    if capability_lookup is None:
        return True
    return property_id in capability_lookup(fixture_id)


def _expand_color_preset_stream(
    raw: dict[str, list],
    segment_count: int,
) -> dict[str, list]:
    """Replicate a single-stream colour preset across all fixture segments.

    A colour preset emits one keyframe stream on channel ``"color"``. For a
    multi-segment fixture we need the same stream on every ``color_N``
    output so all segments render the same colour at each tick (per the
    distribution rule's K==1 branch). Manual assignments are already
    expanded by :meth:`ColorProperty.generate_requests` and do not hit
    this path.
    """
    if segment_count <= 1 or "color" not in raw:
        return raw
    stream = raw.pop("color")
    for i in range(segment_count):
        raw[color_channel_name(i, segment_count)] = list(stream)
    return raw


def _collect_cue(cue_index: int, cue: PropertyCue, children: list[ResolvedChild],
                 library: dict[str, EffectPreset] | None,
                 name_resolver: NameResolver,
                 capability_lookup: CapabilityLookup | None,
                 gobo_wheel_count_lookup: GoboWheelCountLookup | None,
                 beam_sub_capabilities_lookup: BeamSubCapabilityLookup | None,
                 color_segment_count_lookup: ColorSegmentCountLookup | None,
                 all_specs: dict[str, ChannelSpec],
                 ) -> tuple[list[RequestGroup], dict[str, ChannelSpec]]:
    from model.virtual_filters.property_cues._default_specs import property_kwargs_for_fixture

    groups: list[RequestGroup] = []
    specs: dict[str, ChannelSpec] = {}
    step_start = 0
    for si, step in enumerate(cue.steps):
        for node_path, assignments in step.assignments.items():
            matches = _resolve_path_children(node_path, children)
            if not matches:
                continue
            depth = len([p for p in node_path.split("/") if p])
            for pid, assignment in assignments.by_property.items():
                for ci, child in matches:
                    # A step- or group-level assignment expands to every matched
                    # child; silently drop children whose fixture doesn't have
                    # the capability so a wash doesn't grow gobo outputs just
                    # because the step-level assignment also covers a spot.
                    if not _child_supports_property(child[0], pid, capability_lookup):
                        continue
                    prefix = _prefix(child[0], child[1], name_resolver)
                    fixture_kwargs = property_kwargs_for_fixture(
                        pid, child[0],
                        gobo_wheel_count_lookup, beam_sub_capabilities_lookup,
                        color_segment_count_lookup,
                    )
                    local_specs = _spec_table_for(pid, prefix, assignment, fixture_kwargs)
                    specs.update(local_specs)
                    try:
                        raw = _emit_requests(assignment, pid, step_start,
                                             step.duration_40hz, ci, library, fixture_kwargs)
                    except ValueError as exc:
                        raise ValueError(
                            f"Cue {cue_index} step {si} property {pid!r}"
                            f" @ {node_path!r}: {exc}",
                        ) from exc
                    if pid == "color":
                        raw = _expand_color_preset_stream(
                            raw, int(fixture_kwargs.get("segment_count", 1)),
                        )
                    prefixed = {f"{prefix}__{n}": r for n, r in raw.items()}
                    if not prefixed:
                        continue
                    # A preset may emit channels for properties *other* than its
                    # ``applies_for`` (``pan_sweep`` writes the dimmer on top of
                    # pan, for instance). Accept those extras as long as the
                    # fixture actually has specs for them -- otherwise they stay
                    # out of ``channel_names`` and the solver drops them, which
                    # is how an unsupported dimmer ask on a gobo-only fixture
                    # goes away silently.
                    claimed = set(local_specs.keys())
                    claimed.update(name for name in prefixed if name in all_specs)
                    groups.append(RequestGroup(
                        origin_label=f"c{cue_index}.s{si}.{pid}.{node_path}",
                        tree_depth=depth,
                        channel_names=frozenset(claimed),
                        requests=prefixed,
                    ))
        step_start += int(step.duration_40hz)
    return groups, specs


def _check_strategy_shadowing(cap: str, prefix: str,
                              strategy_output: PostprocessOutput,
                              raw_locals: set[str]) -> None:
    """Refuse a strategy whose exposed port shadows a raw cue-filter channel.

    ``filter_serialization._create_filter_element_for_fish`` builds a
    channel-override dictionary keyed by ``"{vfilter_id}:{exposed_port}"``
    and applies it to every filter's ``channel_links``. If a post-processing
    strategy publishes a port with the same local name as a raw channel it
    reads from the native cue filter, the override rewrites the strategy's
    own internal input to point at the strategy's own output -- a self-link
    that stalls fish's scheduler.

    Pan/tilt and (now) dimmer avoid this by giving the raw channel a distinct
    name (``pan_value`` / ``brightness_raw``) and adding a
    ``SYNTHESIZED_OUTPUTS`` entry for the exposed name. The passthrough
    strategy (no filters, exposed name == raw name) is allowed because it
    doesn't introduce an override.
    """
    if not strategy_output.filters:
        return
    for exposed_name in strategy_output.external_ports:
        if exposed_name in raw_locals:
            raise ValueError(
                f"Post-processing strategy for capability {cap!r} on prefix "
                f"{prefix!r} exposes port {exposed_name!r} which is also a raw "
                f"channel name produced by the property. After serialisation the "
                f"vfilter's channel_override_dict would rewrite every reference to "
                f"{exposed_name!r} -- including the strategy's own internal "
                f"inputs -- creating a filter whose channel_links reference its "
                f"own output. Rename the raw channel, add it to "
                f"INTERNAL_LOCAL_NAMES, and expose the external name via "
                f"SYNTHESIZED_OUTPUTS (see the pan_value/pan or "
                f"brightness_raw/brightness pair for the pattern).",
            )


_CONSTANT_TYPE_FOR_DT: dict[DataType, FilterTypeEnumeration] = {
    DataType.DT_8_BIT: FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
    DataType.DT_16_BIT: FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
    DataType.DT_DOUBLE: FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
    DataType.DT_COLOR: FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
}
_DEFAULT_VALUE_STRING_FOR_DT: dict[DataType, str] = {
    DataType.DT_8_BIT: "0",
    DataType.DT_16_BIT: "0",
    DataType.DT_DOUBLE: "0.0",
    DataType.DT_COLOR: "0,0,0",
}


def _default_value_for(spec: ChannelSpec) -> str:
    """Return the value a defaulted channel should carry on its constant filter."""
    return spec.default_value or _DEFAULT_VALUE_STRING_FOR_DT.get(spec.data_type, "0")


def _constant_filter_for_defaulted(
    canonical: str, spec: ChannelSpec, cue_filter_id: str, scene: Scene,
    pos: tuple[int, int] | tuple[float, float] | None,
) -> Filter:
    """Materialise a ``FILTER_CONSTANT_*`` carrying the canonical's default value."""
    const_type = _CONSTANT_TYPE_FOR_DT.get(
        spec.data_type, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
    )
    const_id = f"{cue_filter_id}__CONST__{canonical}"
    const = construct_filter_instance(
        scene, int(const_type), const_id, pos=pos,
    )
    const.initial_parameters["value"] = _default_value_for(spec)
    return const


def _detect_defaulted_canonicals(
    all_specs: dict[str, ChannelSpec], consolidation: ConsolidationMap,
    per_cue_frames: dict[str, dict[str, list[KeyFrame]]],
) -> set[str]:
    """Return the canonical channels that have no keyframes in any cue."""
    canonicals = {consolidation.canonical(n) for n in all_specs}
    defaulted: set[str] = set()
    for canonical in canonicals:
        has_frames = any(
            per_cue_frames.get(cue_id, {}).get(canonical)
            for cue_id in per_cue_frames
        )
        if not has_frames:
            defaulted.add(canonical)
    return defaulted


def _collect_constant_inputs(
    canonical_prefix: str, cap: str,
    all_specs: dict[str, ChannelSpec],
    defaulted_canonicals: set[str],
    consolidation: ConsolidationMap,
    ch_capability: dict[str, str],
) -> dict[str, str]:
    """Return ``{local_name: default_value_str}`` for raw channels in a defaulted canonical group.

    Covers every raw channel in this ``(prefix, capability)`` group whose canonical
    is defaulted. Empty dict if any raw channel in the group is live -- strategies
    only fold when **every** input is static.
    """
    out: dict[str, str] = {}
    for spec_name, spec in all_specs.items():
        prefix, _, local = spec_name.partition("__")
        if prefix != canonical_prefix:
            continue
        if ch_capability.get(spec_name) != cap:
            continue
        canonical = consolidation.canonical(spec_name)
        if canonical not in defaulted_canonicals:
            return {}  # live input in this group -- cannot fold
        out[local] = _default_value_for(spec)
    return out


def _build_ports(all_specs: dict[str, ChannelSpec], consolidation: ConsolidationMap,
                 ch_capability: dict[str, str], ch_prefix: dict[str, str],
                 cue_filter_id: str, scene: Scene,
                 pos: tuple[int, int] | tuple[float, float] | None,
                 defaulted_canonicals: set[str],
                 defaulted_source_map: dict[str, str],
                 ) -> tuple[list[Filter], dict[str, tuple[str, str]]]:
    pp_filters: list[Filter] = []
    external_ports: dict[str, tuple[str, str]] = {}
    raw_locals = {name.partition("__")[2] for name in all_specs}
    # Cache the post-process chain per (canonical_prefix, capability) so a
    # consolidated sibling prefix can reuse the canonical strategy's output
    # ports without re-building a second chain. Before the dimmer rename made
    # raw and exposed names distinct, the sibling case fell through to the
    # native cue filter channel (which only resolved correctly because raw
    # and exposed names happened to match).
    cached_strategies: dict[tuple[str, str], PostprocessOutput] = {}
    for virtual_name in sorted(all_specs.keys()):
        canonical = consolidation.canonical(virtual_name)
        virtual_prefix = virtual_name.partition("__")[0]
        canonical_prefix = ch_prefix[canonical]
        cap = ch_capability[virtual_name]
        key = (canonical_prefix, cap)
        if key not in cached_strategies:
            const_inputs = _collect_constant_inputs(
                canonical_prefix, cap, all_specs, defaulted_canonicals,
                consolidation, ch_capability,
            )
            out = build_postprocess_chain(cap, CapabilityContext(
                scene=scene, cue_filter_id=cue_filter_id,
                channel_name_prefix=canonical_prefix, pos=pos,
                constant_inputs=const_inputs,
            ))
            _check_strategy_shadowing(cap, canonical_prefix, out, raw_locals)
            # Rewrite any strategy-internal references to defaulted raw
            # channels so they read from the constant filter the compiler
            # emitted for that channel, not from the (now absent) native
            # cue filter output.
            for pp_filter in out.filters:
                for input_port, source in list(pp_filter.channel_links.items()):
                    override = defaulted_source_map.get(source)
                    if override is not None:
                        pp_filter.channel_links[input_port] = override
            pp_filters.extend(out.filters)
            cached_strategies[key] = out
        out = cached_strategies[key]
        for cap_name, port in out.external_ports.items():
            # Publish the strategy's output under the virtual prefix so both
            # the canonical and the consolidated siblings expose the gated
            # port (e.g. MH1__brightness and MH2__brightness both point at
            # the MH1 strobe generator when their timelines consolidated).
            port_fid, port_ch = port
            if (
                port_fid == cue_filter_id
                and port_ch in defaulted_canonicals
            ):
                # Passthrough-style strategies (focus / frost / gobo / colour /
                # a beam fixture with no sub-caps) publish their external port
                # as a direct reference to a channel on the native cue filter.
                # When that channel is defaulted it was pulled OFF the cue
                # filter and materialised as a standalone constant; redirect
                # the external port onto the constant so downstream
                # ``channel_override_dict`` entries don't end up mapping
                # ``cue_filter:ch`` to itself (which fish then rejects with
                # ``corresponding output channel wasn't found``).
                const_ref = defaulted_source_map[f"{cue_filter_id}:{port_ch}"]
                const_id, _, const_port_name = const_ref.partition(":")
                resolved_port = (const_id, const_port_name)
            else:
                resolved_port = port
            external_ports.setdefault(f"{virtual_prefix}__{cap_name}", resolved_port)
        # Passthrough fallback: for raw channels the vfilter still has to be
        # addressable by, point at the native cue filter unless the channel
        # was defaulted -- in which case point at the constant filter the
        # compiler emitted for it.
        if canonical in defaulted_canonicals:
            source_ref = defaulted_source_map[f"{cue_filter_id}:{canonical}"]
            const_id, _, const_port = source_ref.partition(":")
            external_ports.setdefault(virtual_name, (const_id, const_port))
        else:
            external_ports.setdefault(virtual_name, (cue_filter_id, canonical))
    return pp_filters, external_ports


def compile_property_model(
    model: PropertyCueFilterModel, cue_filter_id: str, scene: Scene,
    preset_library: dict[str, EffectPreset] | None = None,
    pos: tuple[int, int] | tuple[float, float] | None = None,
    fixture_resolver: FixtureResolver | None = None,
    name_resolver: NameResolver | None = None,
    capability_lookup: CapabilityLookup | None = None,
    gobo_wheel_count_lookup: GoboWheelCountLookup | None = None,
    beam_sub_capabilities_lookup: BeamSubCapabilityLookup | None = None,
    color_segment_count_lookup: ColorSegmentCountLookup | None = None,
) -> CompileResult:
    """See module docstring."""
    children = (fixture_resolver or _default_resolver)(model.fixture_selection)
    name_fn = name_resolver or _default_name_resolver
    all_specs: dict[str, ChannelSpec] = default_specs_for_fixtures(
        model.fixture_selection, children,
        lambda fid, segment: _prefix(fid, segment, name_fn),
        capability_lookup, gobo_wheel_count_lookup, beam_sub_capabilities_lookup,
        color_segment_count_lookup,
    )
    per_cue: list[tuple[int, str, list[RequestGroup]]] = []
    for cue_index, cue in enumerate(model.cues):
        groups, specs = _collect_cue(
            cue_index, cue, children, preset_library, name_fn,
            capability_lookup, gobo_wheel_count_lookup, beam_sub_capabilities_lookup,
            color_segment_count_lookup,
            all_specs,
        )
        all_specs.update(specs)
        per_cue.append((cue_index, cue.name or f"Cue {cue_index + 1}", groups))
    solver = KeyframeSolver()
    per_cue_frames: dict[str, dict[str, list[KeyFrame]]] = {}
    for cue_index, _n, groups in per_cue:
        solved = solver.solve(SolveInput(channel_specs=all_specs, groups=groups))
        per_cue_frames[f"cue_{cue_index}"] = {n: s.frames for n, s in solved.items()}
    ch_prefix = {n: n.partition("__")[0] for n in all_specs}
    ch_capability = {n: _infer_capability(n.partition("__")[2]) for n in all_specs}
    pp_sigs = {n: f"{ch_capability[n]}:None:None" for n in all_specs}
    consolidation = consolidate(per_cue_frames, all_specs, pp_sigs)
    # Detect canonical channels that have no keyframes anywhere; emit a
    # ``FILTER_CONSTANT_*`` for each so the native cue filter doesn't have to
    # carry a channel whose only purpose is to publish its own default. A
    # live canonical with the same local name on a sibling prefix still has
    # frames in its own stream and stays on the cue filter untouched.
    defaulted_canonicals = _detect_defaulted_canonicals(
        all_specs, consolidation, per_cue_frames,
    )
    defaulted_source_map: dict[str, str] = {}
    constant_filters: list[Filter] = []
    for canonical in sorted(defaulted_canonicals):
        const = _constant_filter_for_defaulted(
            canonical, all_specs[canonical], cue_filter_id, scene, pos,
        )
        constant_filters.append(const)
        defaulted_source_map[f"{cue_filter_id}:{canonical}"] = f"{const.filter_id}:value"
    native_model = build_native(
        model, consolidation, all_specs, per_cue, per_cue_frames,
        skip_canonicals=defaulted_canonicals,
    )
    pp_filters, external_ports = _build_ports(
        all_specs, consolidation, ch_capability, ch_prefix, cue_filter_id, scene, pos,
        defaulted_canonicals=defaulted_canonicals,
        defaulted_source_map=defaulted_source_map,
    )
    pp_filters = constant_filters + list(pp_filters)
    return CompileResult(
        native_model=native_model, postprocess_filters=tuple(pp_filters),
        consolidation=consolidation, external_ports=external_ports,
        channel_specs=all_specs,
    )
