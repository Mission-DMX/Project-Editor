"""Live preview for the property-based cue vfilter.

Instantiates one FILTER_CONSTANT_* per output channel and runs a QThread that
evaluates the model at the editor's time cursor, sending per-tick GUI updates
to Fish via NetworkManager.
"""

from __future__ import annotations

import weakref
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal

from controller.network import NetworkManager
from model.color_hsi import ColorHSI
from model.filter import DataType, Filter, FilterTypeEnumeration
from model.filter_data.cues.curves import value_at
from model.filter_data.transfer_function import TransferFunction
from model.filters.factory import construct_filter_instance

if TYPE_CHECKING:
    from model import Scene
    from model.filter_data.cues.cue import Cue, KeyFrame
    from model.virtual_filters.property_cues.channel_consolidator import ConsolidationMap
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

logger = getLogger(__name__)


_LIVE_THREADS: weakref.WeakSet[PropertyCuesPreviewThread] = weakref.WeakSet()


def shutdown_all_preview_threads(timeout_ms: int = 500) -> None:
    """Ask any still-running preview thread to stop and wait briefly for it."""
    for t in list(_LIVE_THREADS):
        try:
            if t.isRunning():
                t.requestInterruption()
                t.wait(timeout_ms)
        except RuntimeError:
            pass


_CONSTANT_FILTER_TYPE: dict[DataType, FilterTypeEnumeration] = {
    # Each spec's data type picks a *same-width* constant so the cloned
    # postprocess chain's typed inputs still line up with fish's expected
    # widths. Previously ``DT_8_BIT`` was mapped to the 16-bit constant and
    # fish rejected the pan/tilt switch with ``channel mapping does not
    # contain channel 'select' of type 'uint8_t'`` -- the switch's select
    # input is uint8 but the preview_const feeding it was uint16.
    DataType.DT_8_BIT: FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
    DataType.DT_16_BIT: FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
    DataType.DT_DOUBLE: FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
    DataType.DT_BOOL: FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
    DataType.DT_COLOR: FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
}


_DEFAULT_VALUE_FOR_DT: dict[DataType, str] = {
    DataType.DT_8_BIT: "0",
    DataType.DT_16_BIT: "0",
    DataType.DT_DOUBLE: "0.0",
    DataType.DT_BOOL: "0",
    DataType.DT_COLOR: "0,0,0",
}


def build_preview_filters(
    vfilter: PropertyBasedCueFilter,
    scene: Scene,
    filter_list: list[Filter],
) -> dict[str, str]:
    """Instantiate the preview filter graph and return the output-port mapping.

    For every virtual output port that the production serializer would resolve
    to a channel on the native cue filter, a ``FILTER_CONSTANT_*`` with id
    ``{cue_fid}__PREVIEW_CONST__{canonical}`` takes the cue filter's place and
    the preview thread writes per-tick values into it. The postprocess chain
    (sin/cos/switch/range for pan/tilt, strobe-fold for dimmer, etc.) is
    *cloned* into the preview scene with its channel_links rewritten to read
    from those PREVIEW_CONSTs, so synthesized outputs like ``X__pan`` keep
    being produced by the same chain the production show runs -- the only
    difference is that the chain's raw inputs now come from the preview
    constants rather than the native cue filter.

    The returned mapping covers **both** raw virtual names (``X__color``,
    ``X__pan_value``, ...) and synthesized virtual names (``X__pan``,
    ``X__brightness``, ...), so ``PreviewFilter.resolve_output_port_id``
    always finds a downstream-visible filter to point to.
    """
    res = vfilter._ensure_compiled()
    cue_fid = vfilter.filter_id
    specs = res.channel_specs
    consolidation = res.consolidation

    # Pass 1 — walk the compile's external_ports. Entries that still point at
    # the native cue filter (``port_fid == cue_fid``) materialise a
    # PREVIEW_CONST on demand; everything else (defaulted CONSTs, strategy
    # outputs) already resolves to something we're going to emit, so we
    # just copy the reference through unchanged.
    canonical_to_const_id: dict[str, str] = {}
    mapping: dict[str, str] = {}
    for virtual_name, (port_fid, port_ch) in res.external_ports.items():
        if port_fid != cue_fid:
            mapping[virtual_name] = f"{port_fid}:{port_ch}"
            continue
        canonical = port_ch
        if canonical not in canonical_to_const_id:
            spec = specs.get(canonical) or specs.get(virtual_name)
            if spec is None:
                continue
            const_type = _CONSTANT_FILTER_TYPE.get(
                spec.data_type, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            )
            const_id = f"{cue_fid}__PREVIEW_CONST__{canonical}"
            const_filter = Filter(scene, const_id, filter_type=int(const_type), pos=vfilter.pos)
            # Seed with the spec's default (or a sensible per-type zero) so
            # fish accepts the filter at configure time. Live cues override
            # this on the first preview tick anyway.
            const_filter.initial_parameters["value"] = (
                spec.default_value or _DEFAULT_VALUE_FOR_DT.get(spec.data_type, "0")
            )
            filter_list.append(const_filter)
            canonical_to_const_id[canonical] = const_id
        mapping[virtual_name] = f"{canonical_to_const_id[canonical]}:value"

    # Pass 2 — clone the postprocess chain into the preview scene and rewrite
    # every ``{cue_fid}:{canonical}`` channel_link to read from the matching
    # PREVIEW_CONST we just created. References to the compile's ``CONST``
    # filters (defaulted canonicals) start with ``{cue_fid}__CONST__``, not
    # ``{cue_fid}:``, so the startswith guard leaves them untouched.
    for pp_src in res.postprocess_filters:
        pp_clone = construct_filter_instance(
            scene=scene,
            filter_type=int(pp_src.filter_type),
            filter_id=pp_src.filter_id,
            pos=pp_src.pos,
            filter_configurations=dict(pp_src.filter_configurations),
            initial_parameters=dict(pp_src.initial_parameters),
        )
        if pp_clone is None:
            # The factory returns None for legacy virtual-filter types that
            # haven't been migrated. Fall back to a plain Filter so the chain
            # at least keeps its shape.
            pp_clone = Filter(scene, pp_src.filter_id, filter_type=int(pp_src.filter_type), pos=pp_src.pos)
            pp_clone.filter_configurations.update(pp_src.filter_configurations)
            pp_clone.initial_parameters.update(pp_src.initial_parameters)
        for input_port, source in pp_src.channel_links.items():
            pp_clone.channel_links[input_port] = _preview_rewrite(
                source, cue_fid, consolidation, canonical_to_const_id,
            )
        filter_list.append(pp_clone)

    return mapping


def _preview_rewrite(
    source: str, cue_fid: str,
    consolidation: ConsolidationMap, canonical_to_const_id: dict[str, str],
) -> str:
    """Rewrite one strategy channel_link from cue-filter ref to PREVIEW_CONST ref."""
    if not source:
        return source
    prefix = f"{cue_fid}:"
    if not source.startswith(prefix):
        return source
    local = source[len(prefix):]
    canonical = consolidation.canonical(local)
    const_id = canonical_to_const_id.get(canonical)
    return f"{const_id}:value" if const_id else source


def _pick_cue(vfilter: PropertyBasedCueFilter, index: int) -> Cue | None:
    res = vfilter._last_compile
    if res is None:
        return None
    cues = res.native_model.cues
    if not cues:
        return None
    if index < 0 or index >= len(cues):
        index = max(0, min(index, len(cues) - 1))
    return cues[index]


def _value_at_time(
    frames: list[KeyFrame], channel_index: int, t: float,
) -> float | ColorHSI | None:
    """Interpolate the state of ``channel_index`` at timecode ``t``.

    Returns None if frames is empty or the channel is not present in the frame.
    """
    if not frames:
        return None
    if t <= frames[0].timestamp:
        kf = frames[0]
        return kf._states[channel_index]._value if channel_index < len(kf._states) else None
    if t >= frames[-1].timestamp:
        kf = frames[-1]
        return kf._states[channel_index]._value if channel_index < len(kf._states) else None
    prev = frames[0]
    nxt = frames[-1]
    for i in range(1, len(frames)):
        if frames[i].timestamp >= t:
            prev = frames[i - 1]
            nxt = frames[i]
            break
    if channel_index >= len(prev._states) or channel_index >= len(nxt._states):
        return None
    span = nxt.timestamp - prev.timestamp
    rel = 0.0 if span <= 0.0 else (t - prev.timestamp) / span
    try:
        transition = TransferFunction(nxt._states[channel_index]._transition_type)
    except ValueError:
        transition = TransferFunction.LINEAR
    return value_at(rel, prev._states[channel_index], nxt._states[channel_index], transition)


def _format_value(value: float | ColorHSI, data_type: DataType) -> str:
    if isinstance(value, ColorHSI):
        return value.format_for_filter()
    if data_type == DataType.DT_DOUBLE:
        return str(float(value))
    return str(int(value))


class PropertyCuesPreviewThread(QThread):
    """Reads the compiled model and emits constant updates at ``tick_hz``."""

    tick_rendered = Signal(float)

    def __init__(
        self,
        vfilter: PropertyBasedCueFilter,
        channel_filter_map: dict[str, str],
        tick_hz: float = 24.0,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._vfilter_ref = weakref.ref(vfilter)
        # Strip the ":value" suffix if present — we add it back when sending.
        self._channel_filter_map: dict[str, str] = {}
        for virtual_port, mapped in channel_filter_map.items():
            self._channel_filter_map[virtual_port] = mapped.split(":", 1)[0]
        self._scene_id = vfilter.scene.scene_id
        self._tick_hz = max(1.0, float(tick_hz))
        self._timecode = 0.0
        self._playing = False
        self._cue_index = 0
        _LIVE_THREADS.add(self)
        self.finished.connect(self.deleteLater)

    def set_timecode(self, seconds: float) -> None:
        self._timecode = float(seconds)

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)

    def set_cue_index(self, index: int) -> None:
        self._cue_index = int(index)

    def run(self) -> None:
        """Main loop: at ``_tick_hz``, evaluate the current cue and send updates."""
        tick_ms = max(1, int(1000.0 / self._tick_hz))
        nm = NetworkManager()
        while not self.isInterruptionRequested():
            if self._playing:
                self._emit_tick(nm)
            self.msleep(tick_ms)

    def _emit_tick(self, nm: NetworkManager) -> None:
        vfilter = self._vfilter_ref()
        if vfilter is None:
            return
        cue = _pick_cue(vfilter, self._cue_index)
        if cue is None:
            return
        frames = list(cue._frames)
        if not frames:
            return
        # Build canonical -> channel index map using cue._channel_definitions.
        canonical_to_index: dict[str, int] = {
            name: i for i, (name, _dt) in enumerate(cue._channel_definitions)
        }
        canonical_to_dt: dict[str, DataType] = dict(cue._channel_definitions)
        res = vfilter._last_compile
        if res is None:
            return
        consolidation = res.consolidation
        emitted: set[str] = set()
        for virtual_port, const_id in self._channel_filter_map.items():
            if const_id in emitted:
                continue
            canonical = consolidation.canonical(virtual_port)
            idx = canonical_to_index.get(canonical)
            if idx is None:
                continue
            value = _value_at_time(frames, idx, self._timecode)
            if value is None:
                continue
            dt = canonical_to_dt.get(canonical, DataType.DT_DOUBLE)
            payload = _format_value(value, dt)
            try:
                nm.send_gui_update_to_fish(
                    self._scene_id, const_id, "value", payload, enque=True,
                )
            except RuntimeError as exc:
                logger.debug("Preview update failed for %s: %s", const_id, exc)
                continue
            emitted.add(const_id)
        self.tick_rendered.emit(self._timecode)
