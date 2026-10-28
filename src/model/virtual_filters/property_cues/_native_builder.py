"""Build the native CueFilterModel from solved per-cue keyframe streams."""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter_data.cues.cue import Cue, EndAction, KeyFrame
from model.filter_data.cues.cue_filter_model import CueFilterModel
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.model.model import EndAction as ModelEndAction
from model.virtual_filters.property_cues.solver_helpers import make_frame

if TYPE_CHECKING:
    from model.filter import DataType
    from model.filter_data.cues.cue import State
    from model.virtual_filters.property_cues.channel_consolidator import ConsolidationMap
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.solver import RequestGroup

_END_ACTION_MAP = {ModelEndAction.HOLD: EndAction.HOLD,
                   ModelEndAction.START_AGAIN: EndAction.START_AGAIN,
                   ModelEndAction.NEXT_CUE: EndAction.NEXT}


def _parse_end(value: str) -> ModelEndAction:
    try:
        return ModelEndAction(value)
    except ValueError:
        return ModelEndAction.HOLD


def _state_for(ch_name: str, dt: DataType, ts: float, frames: list[KeyFrame]) -> State:
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
                   end_action: ModelEndAction, restart_on_play: bool) -> Cue:
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
    cue.end_action = _END_ACTION_MAP.get(end_action, EndAction.HOLD)
    cue.restart_on_another_play_press = restart_on_play
    return cue


def build_native(model: PropertyCueFilterModel, consolidation: ConsolidationMap,
                 all_specs: dict[str, ChannelSpec],
                 per_cue: list[tuple[int, str, list[RequestGroup]]],
                 per_cue_frames: dict[str, dict[str, list[KeyFrame]]]) -> CueFilterModel:
    canonical_channels = sorted({consolidation.canonical(n) for n in all_specs})
    sorted_channels = [(n, all_specs[n].data_type) for n in canonical_channels]
    native = CueFilterModel()
    for n, dt in sorted_channels:
        native.add_channel(n, dt)
    native.global_restart_on_end = False
    native.persistence_enabled = model.general.persistence
    for (cue_index, cue_name, _groups), src_cue in zip(per_cue, model.cues, strict=True):
        canonical_frames: dict[str, list[KeyFrame]] = {n: [] for n in canonical_channels}
        for v_name, frames in per_cue_frames[f"cue_{cue_index}"].items():
            canonical_frames.setdefault(consolidation.canonical(v_name), []).extend(frames)
        for frames in canonical_frames.values():
            frames.sort(key=lambda kf: kf.timestamp)
        native.cues.append(_frames_to_cue(
            cue_name, sorted_channels, canonical_frames,
            _parse_end(src_cue.end_action), src_cue.restart_on_play,
        ))
    if 0 <= model.general.default_cue_index < len(native.cues):
        native.default_cue = model.general.default_cue_index
    return native
