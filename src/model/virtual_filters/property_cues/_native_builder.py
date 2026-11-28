"""Build the native CueFilterModel from solved per-cue keyframe streams."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.cues import curves
from model.filter_data.cues.cue import Cue, EndAction, KeyFrame, State
from model.filter_data.cues.cue_filter_model import CueFilterModel
from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from model.virtual_filters.property_cues.channel_consolidator import ConsolidationMap
    from model.virtual_filters.property_cues.channel_spec import ChannelSpec
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
    from model.virtual_filters.property_cues.solver import RequestGroup


def _parse_default(dt: DataType, default_value: str) -> Union[float, int, ColorHSI]:
    """Parse a :class:`ChannelSpec` ``default_value`` string into a typed value.

    Falls back to a per-type zero if the string is missing or malformed, so
    the caller always gets a value compatible with ``State.from_value``.
    """
    if dt is DataType.DT_COLOR:
        if default_value:
            parts = default_value.split(",")
            if len(parts) == 3:
                try:
                    return ColorHSI(float(parts[0]), float(parts[1]), float(parts[2]))
                except (ValueError, TypeError):
                    pass
        return ColorHSI(0.0, 0.0, 0.0)
    if dt is DataType.DT_DOUBLE:
        try:
            return float(default_value) if default_value else 0.0
        except (ValueError, TypeError):
            return 0.0
    try:
        return int(default_value) if default_value else 0
    except (ValueError, TypeError):
        return 0


_SLOT_SECONDS = 1.0 / 40.0


def _state_for(spec: ChannelSpec, ts: float, frames: list[KeyFrame]) -> State:
    """Return the state for ``spec`` at timestamp ``ts``.

    When ``ts`` falls between two keyframes on this channel, interpolate
    using :func:`curves.value_at` with the **next** frame's transition (F1 --
    matches fish's and the preview's semantics). Without this an unrelated
    cross-channel keyframe used to turn a running fade into a hold.

    Fallback value when no keyframe has been emitted yet comes from
    ``spec.default_value`` rather than a hard-coded 0, so e.g. the duty cycle's
    documented default of 128 is honoured.
    """
    hit = next((kf for kf in frames if round(kf.timestamp, 6) == ts), None)
    if hit is not None and hit._states:
        return hit._states[0].copy()
    prior = [kf for kf in frames if kf.timestamp < ts]
    nxt = next((kf for kf in frames if kf.timestamp > ts), None)
    if prior and nxt and prior[-1]._states and nxt._states:
        prev_kf = prior[-1]
        span = nxt.timestamp - prev_kf.timestamp
        rel = 0.0 if span <= 0.0 else (ts - prev_kf.timestamp) / span
        try:
            transition = TransferFunction(nxt._states[0]._transition_type)
        except (ValueError, TypeError):
            transition = TransferFunction.LINEAR
        try:
            value = curves.value_at(rel, prev_kf._states[0], nxt._states[0], transition)
        except ValueError:
            return prev_kf._states[0].copy()
        return State.from_value(spec.data_type, transition, value)
    if prior and prior[-1]._states:
        return prior[-1]._states[0].copy()
    return State.from_value(
        spec.data_type, TransferFunction.LINEAR,
        _parse_default(spec.data_type, spec.default_value),
    )


def _densify_non_linear(
    spec: ChannelSpec, frames: list[KeyFrame],
) -> list[KeyFrame]:
    """Densify segments whose next-frame transition is non-linear.

    Fish stores keyframes sparsely and uses the target frame's transition to
    interpolate between them. For LINEAR / EDGE segments the engine's
    interpolation matches our :func:`curves.value_at` evaluation exactly so
    one pair of frames is enough. For SIGMOIDAL / EASE_IN / EASE_OUT the
    exact shape between two sparse keyframes depends on the full span --
    splitting such a segment at an unrelated cross-channel slot would
    silently flatten the curve (slot 25 of a 0..100 sigmoid would read 0.25
    instead of 0.045).

    We emit intermediate samples at every 40 Hz tick within non-linear
    spans so fish's piecewise-linear evaluation between consecutive samples
    is a close approximation of the authored curve. The number of extra
    frames is bounded by the span: a 2 s sigmoid fade adds 79 samples,
    which is cheap at compile time and negligible at runtime.
    """
    if len(frames) < 2:
        return list(frames)
    densified: list[KeyFrame] = []
    for i, frame in enumerate(frames):
        densified.append(frame)
        if i + 1 >= len(frames):
            continue
        nxt = frames[i + 1]
        if not frame._states or not nxt._states:
            continue
        try:
            transition = TransferFunction(nxt._states[0]._transition_type)
        except (ValueError, TypeError):
            continue
        if transition in (TransferFunction.LINEAR, TransferFunction.EDGE):
            continue
        span = nxt.timestamp - frame.timestamp
        if span <= _SLOT_SECONDS:
            continue
        tick_count = max(1, round(span * 40.0))
        for tick in range(1, tick_count):
            rel = tick / tick_count
            try:
                value = curves.value_at(rel, frame._states[0], nxt._states[0], transition)
            except ValueError:
                break
            # These scratch frames never enter the cue directly; they only
            # feed :func:`_state_for` so the combined-slot iteration picks
            # up densely-sampled values at every 40 Hz tick.
            sample = KeyFrame.at(
                frame.timestamp + tick * _SLOT_SECONDS,
                states=[State.from_value(spec.data_type, TransferFunction.LINEAR, value)],
            )
            densified.append(sample)
    return densified


def _frames_to_cue(name: str, channels: list[ChannelSpec],
                   per_channel: dict[str, list[KeyFrame]],
                   end_action: EndAction, restart_on_play: bool) -> Cue:
    cue = Cue()
    cue.name = name or "No Name"
    for spec in channels:
        cue.add_channel(spec.name, spec.data_type)
    # Densify non-linear segments before building the combined-slot union so
    # cross-channel interpolation never lands at a point where fish's
    # piecewise linear evaluation would distort the authored curve.
    densified: dict[str, list[KeyFrame]] = {
        spec.name: _densify_non_linear(spec, per_channel.get(spec.name, []))
        for spec in channels
    }
    slots: set[float] = {round(kf.timestamp, 6) for frames in densified.values() for kf in frames}
    if not slots:
        slots.add(0.0)
    for ts in sorted(slots):
        combined = KeyFrame(cue)
        combined.timestamp = ts
        for spec in channels:
            combined._states.append(_state_for(spec, ts, densified.get(spec.name, [])))
        cue.insert_frame(combined)
    cue.end_action = end_action
    cue.restart_on_another_play_press = restart_on_play
    return cue


def build_native(model: PropertyCueFilterModel, consolidation: ConsolidationMap,
                 all_specs: dict[str, ChannelSpec],
                 per_cue: list[tuple[int, str, list[RequestGroup]]],
                 per_cue_frames: dict[str, dict[str, list[KeyFrame]]],
                 skip_canonicals: set[str] | None = None,
                 ) -> CueFilterModel:
    """Build the native CueFilterModel.

    ``skip_canonicals`` lists canonical channel names that must NOT appear
    on the native cue filter. The compiler passes defaulted canonicals so
    those channels get materialised as standalone ``FILTER_CONSTANT_*``
    filters instead of carrying an all-zero keyframe stream through the
    cue filter. The native cue filter stays smaller and fish does not see
    a channel it would have to validate without any post-processing
    consumer.
    """
    skip = skip_canonicals or set()
    canonical_channels = sorted(
        {consolidation.canonical(n) for n in all_specs} - skip,
    )
    sorted_specs = [all_specs[n] for n in canonical_channels]
    native = CueFilterModel()
    for spec in sorted_specs:
        native.add_channel(spec.name, spec.data_type)
    native.global_restart_on_end = False
    native.persistence_enabled = model.general.persistence
    for (cue_index, cue_name, _groups), src_cue in zip(per_cue, model.cues, strict=True):
        canonical_frames: dict[str, list[KeyFrame]] = {n: [] for n in canonical_channels}
        for v_name, frames in per_cue_frames[f"cue_{cue_index}"].items():
            canonical = consolidation.canonical(v_name)
            if canonical in skip:
                continue  # defaulted channel is materialised as a constant filter
            canonical_frames.setdefault(canonical, []).extend(frames)
        for frames in canonical_frames.values():
            frames.sort(key=lambda kf: kf.timestamp)
        native.cues.append(_frames_to_cue(
            cue_name, sorted_specs, canonical_frames,
            src_cue.end_action, src_cue.restart_on_play,
        ))
    if 0 <= model.general.default_cue_index < len(native.cues):
        native.default_cue = model.general.default_cue_index
    return native
