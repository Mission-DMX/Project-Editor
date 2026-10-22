"""Translate a PropertyCueFilterModel into native cue filter + postprocess chain + port map."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING

from model.filter import DataType
from model.filter_data.cues.cue import Cue, EndAction, KeyFrame
from model.filter_data.cues.cue_filter_model import CueFilterModel
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_consolidator import ConsolidationMap, consolidate
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.model.fixture_selection import FixtureSelection, SelectionEntryKind
from model.virtual_filters.property_cues.model.model import EndAction as ModelEndAction
from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
from model.virtual_filters.property_cues.model.property_step import (
    ManualPropertyAssignment,
    PresetPropertyAssignment,
    PropertyAssignment,
)
from model.virtual_filters.property_cues.postprocess import CapabilityContext, build_postprocess_chain
from model.virtual_filters.property_cues.presets import evaluate_preset, load_preset_library
from model.virtual_filters.property_cues.properties import (
    BeamProperty,
    ColourProperty,
    DimmerProperty,
    FrostProperty,
    GoboProperty,
    PositionProperty,
    Property,
)
from model.virtual_filters.property_cues.solver import KeyframeSolver, RequestGroup, SolveInput
from model.virtual_filters.property_cues.solver_helpers import make_frame

if TYPE_CHECKING:
    from model import Filter, Scene
    from model.virtual_filters.property_cues.presets import EffectPreset

logger = getLogger(__name__)

ResolvedChild = tuple[str, int | None]
FixtureResolver = Callable[[FixtureSelection], list[ResolvedChild]]

_SANITISE = re.compile(r"[^A-Za-z0-9_]")
_PROPERTY_CLASS: dict[str, type[Property]] = {
    "dimmer": DimmerProperty, "position": PositionProperty,
    "colour": ColourProperty, "color": ColourProperty,
    "beam": BeamProperty, "gobo": GoboProperty, "frost": FrostProperty,
}
_CAPABILITY_FROM_LOCAL: dict[str, str] = {
    "pan": "pan", "tilt": "tilt",
    "brightness": "dimmer", "strobefreq": "dimmer", "color": "colour",
    "focus": "beam", "zoom": "beam", "iris": "beam",
    "prism_selection": "beam", "prism_rotation": "beam",
    "goboslot": "gobo", "goborotation": "gobo", "frost_intensity": "frost",
}
_END_ACTION_MAP = {
    ModelEndAction.HOLD: EndAction.HOLD,
    ModelEndAction.START_AGAIN: EndAction.START_AGAIN,
    ModelEndAction.NEXT_CUE: EndAction.NEXT,
}


@dataclass(slots=True)
class CompileResult:
    native_model: CueFilterModel
    postprocess_filters: tuple[Filter, ...]
    consolidation: ConsolidationMap
    external_ports: dict[str, tuple[str, str]]
    channel_specs: dict[str, ChannelSpec] = field(default_factory=dict)


def _default_resolver(selection: FixtureSelection) -> list[ResolvedChild]:
    return [(e.id, None) for e in selection.entries if e.kind is SelectionEntryKind.FIXTURE]


def _prefix(fixture_id: str, segment: int | None) -> str:
    base = _SANITISE.sub("_", fixture_id)
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


def _build_property(property_id: str, assignment: ManualPropertyAssignment) -> Property:
    cls = _PROPERTY_CLASS.get(property_id)
    if cls is None:
        raise ValueError(f"Unknown property type: {property_id!r}")
    kwargs: dict[str, object] = dict(assignment.values)
    try:
        kwargs["transition"] = TransferFunction(assignment.transition)
    except ValueError:
        kwargs["transition"] = TransferFunction.LINEAR
    try:
        return cls(**kwargs)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"Cannot build {property_id!r} from {assignment.values!r}: {exc}") from exc


def _spec_table_for(property_id: str, prefix: str) -> dict[str, ChannelSpec]:
    cls = _PROPERTY_CLASS.get(property_id)
    if cls is None:
        return {}
    try:
        prop = cls()  # type: ignore[call-arg]
    except TypeError:
        return {}
    return {f"{prefix}__{s.name}": ChannelSpec(
        name=f"{prefix}__{s.name}", data_type=s.data_type,
        default_value=s.default_value, aliases=s.aliases,
    ) for s in prop.channel_specs}


def _emit_requests(
    assignment: PropertyAssignment, property_id: str, step_start: int, step_duration: int,
    child_index: int, library: dict[str, EffectPreset] | None,
) -> dict[str, list]:
    if isinstance(assignment, ManualPropertyAssignment):
        prop = _build_property(property_id, assignment)
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


def _collect_cue(cue_index: int, cue, children: list[ResolvedChild],
                 library: dict[str, EffectPreset] | None,
                 ) -> tuple[list[RequestGroup], dict[str, ChannelSpec]]:
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
                    prefix = _prefix(child[0], child[1])
                    local_specs = _spec_table_for(pid, prefix)
                    specs.update(local_specs)
                    try:
                        raw = _emit_requests(assignment, pid, step_start,
                                             step.duration_40hz, ci, library)
                    except ValueError as exc:
                        raise ValueError(
                            f"Cue {cue_index} step {si} property {pid!r}"
                            f" @ {node_path!r}: {exc}",
                        ) from exc
                    prefixed = {f"{prefix}__{n}": r for n, r in raw.items()}
                    if not prefixed:
                        continue
                    groups.append(RequestGroup(
                        origin_label=f"c{cue_index}.s{si}.{pid}.{node_path}",
                        tree_depth=depth,
                        channel_names=frozenset(local_specs.keys()),
                        requests=prefixed,
                    ))
        step_start += int(step.duration_40hz)
    return groups, specs


def _state_for(ch_name: str, dt: DataType, ts: float, frames: list[KeyFrame]):
    hit = next((kf for kf in frames if round(kf.timestamp, 6) == ts), None)
    if hit is not None and hit._states:
        return hit._states[0].copy()
    prior = [kf for kf in frames if kf.timestamp < ts]
    if prior and prior[-1]._states:
        return prior[-1]._states[0].copy()
    return make_frame(ChannelSpec(name=ch_name, data_type=dt), 0,
                      TransferFunction.LINEAR, 0.0)._states[0]


def _frames_to_cue(name: str, channels: list[tuple[str, DataType]],
                   per_channel: dict[str, list[KeyFrame]],
                   model_end: ModelEndAction) -> Cue:
    cue = Cue()
    cue.name = name or "No Name"
    for ch_name, dt in channels:
        cue.add_channel(ch_name, dt)
    slots: set[float] = {round(kf.timestamp, 6) for frames in per_channel.values() for kf in frames}
    if not slots:
        slots.add(0.0)
    for ts in sorted(slots):
        combined = KeyFrame(cue)
        combined.timestamp = ts
        for ch_name, dt in channels:
            combined._states.append(_state_for(ch_name, dt, ts, per_channel.get(ch_name, [])))
        cue.insert_frame(combined)
    cue.end_action = _END_ACTION_MAP.get(model_end, EndAction.HOLD)
    return cue


def _build_native(model: PropertyCueFilterModel, consolidation: ConsolidationMap,
                  all_specs: dict[str, ChannelSpec],
                  per_cue: list[tuple[int, str, list[RequestGroup]]],
                  per_cue_frames: dict[str, dict[str, list[KeyFrame]]]) -> CueFilterModel:
    canonical_channels = sorted({consolidation.canonical(n) for n in all_specs})
    sorted_channels = [(n, all_specs[n].data_type) for n in canonical_channels]
    native = CueFilterModel()
    for n, dt in sorted_channels:
        native.add_channel(n, dt)
    native.global_restart_on_end = model.general.end_action is ModelEndAction.START_AGAIN
    native.persistence_enabled = model.general.persistence
    for cue_index, cue_name, _groups in per_cue:
        canonical_frames: dict[str, list[KeyFrame]] = {n: [] for n in canonical_channels}
        for v_name, frames in per_cue_frames[f"cue_{cue_index}"].items():
            canonical_frames.setdefault(consolidation.canonical(v_name), []).extend(frames)
        for n in canonical_frames:
            canonical_frames[n].sort(key=lambda kf: kf.timestamp)
        native.cues.append(_frames_to_cue(
            cue_name, sorted_channels, canonical_frames, model.general.end_action,
        ))
    if 0 <= model.general.default_cue_index < len(native.cues):
        native.default_cue = model.general.default_cue_index
    return native


def _build_ports(all_specs: dict[str, ChannelSpec], consolidation: ConsolidationMap,
                 ch_capability: dict[str, str], ch_prefix: dict[str, str],
                 cue_filter_id: str, scene: Scene,
                 pos: tuple[int, int] | tuple[float, float] | None,
                 ) -> tuple[list[Filter], dict[str, tuple[str, str]]]:
    pp_filters: list[Filter] = []
    external_ports: dict[str, tuple[str, str]] = {}
    seen: set[tuple[str, str]] = set()
    for virtual_name in sorted(all_specs.keys()):
        canonical = consolidation.canonical(virtual_name)
        cap, prefix = ch_capability[virtual_name], ch_prefix[canonical]
        if (prefix, cap) not in seen:
            out = build_postprocess_chain(cap, CapabilityContext(
                scene=scene, cue_filter_id=cue_filter_id,
                channel_name_prefix=prefix, pos=pos))
            pp_filters.extend(out.filters)
            seen.add((prefix, cap))
            for cap_name, port in out.external_ports.items():
                external_ports[f"{prefix}__{cap_name}"] = port
        external_ports.setdefault(virtual_name, (cue_filter_id, canonical))
    return pp_filters, external_ports


def compile_property_model(
    model: PropertyCueFilterModel, cue_filter_id: str, scene: Scene,
    preset_library: dict[str, EffectPreset] | None = None,
    pos: tuple[int, int] | tuple[float, float] | None = None,
    fixture_resolver: FixtureResolver | None = None,
) -> CompileResult:
    """See module docstring."""
    children = (fixture_resolver or _default_resolver)(model.fixture_selection)
    all_specs: dict[str, ChannelSpec] = {}
    per_cue: list[tuple[int, str, list[RequestGroup]]] = []
    for cue_index, cue in enumerate(model.cues):
        groups, specs = _collect_cue(cue_index, cue, children, preset_library)
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
    native_model = _build_native(model, consolidation, all_specs, per_cue, per_cue_frames)
    pp_filters, external_ports = _build_ports(
        all_specs, consolidation, ch_capability, ch_prefix, cue_filter_id, scene, pos,
    )
    return CompileResult(
        native_model=native_model, postprocess_filters=tuple(pp_filters),
        consolidation=consolidation, external_ports=external_ports,
        channel_specs=all_specs,
    )
