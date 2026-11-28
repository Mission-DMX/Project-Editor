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

    Materialises one ``FILTER_CONSTANT_*`` named
    ``{cue_fid}__PREVIEW_CONST__{canonical}`` for **every** canonical the
    compile knows about -- including canonicals the compiler would normally
    evict as "defaulted" (no keyframes anywhere) and replace with a
    standalone ``__CONST__`` outside the writable set. In preview mode we
    want every channel the thread may push against to resolve to a filter
    that fish actually has in the serialized scene, so the eviction is
    reversed here: the standalone CONSTs are dropped from the clone pass
    and the PREVIEW_CONSTs take their place.

    The postprocess chain (sin/cos/switch/range for pan/tilt, strobe-fold
    for dimmer, colour→wheel, etc.) is cloned into the preview scene with
    every ``{cue_fid}:{raw}`` and ``{cue_fid}__CONST__{canonical}:value``
    channel_link rewritten to read from the matching PREVIEW_CONST, so
    synthesised outputs like ``X__pan`` keep being produced by the same
    chain the production show runs.

    The returned mapping covers **both** raw virtual names (``X__color_0``,
    ``X__pan_value``, ...) and synthesised virtual names (``X__pan``,
    ``X__brightness``, ...), so ``PreviewFilter.resolve_output_port_id``
    always finds a downstream-visible filter to point to.
    """
    res = vfilter._ensure_compiled()
    cue_fid = vfilter.filter_id
    specs = res.channel_specs
    consolidation = res.consolidation

    # Pass 1 — materialise a PREVIEW_CONST per canonical channel.
    #
    # Iterating the deduplicated, sorted canonical set keeps two compile
    # runs of the same model producing bit-identical filter ids. We emit
    # one PREVIEW_CONST per canonical even when the compile marked it as
    # defaulted, so every mapping entry the preview thread later pushes
    # to lands on a filter fish has.
    canonical_to_const_id: dict[str, str] = {}
    canonicals = sorted({consolidation.canonical(n) for n in specs})
    for canonical in canonicals:
        # The canonical (``min(members)`` from consolidation) is itself a
        # virtual_name that lives in ``specs``; no fallback needed.
        spec = specs.get(canonical)
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

    # Build the virtual_name → "{const_id}:value" mapping. Every virtual
    # port whose canonical we just materialised resolves to that
    # PREVIEW_CONST, regardless of what the compile's production
    # ``external_ports`` entry would have been (cue filter, defaulted
    # CONST, or passthrough). The thread writes "value" into exactly
    # those PREVIEW_CONSTs.
    mapping: dict[str, str] = {}
    for virtual_name in specs:
        canonical = consolidation.canonical(virtual_name)
        const_id = canonical_to_const_id.get(canonical)
        if const_id is not None:
            mapping[virtual_name] = f"{const_id}:value"
    # Also publish strategy-level virtual names (``{prefix}__color``,
    # ``{prefix}__pan``, etc.) that resolve to a post-processed strategy
    # output. The thread never writes to these (it feeds raw inputs into
    # the chain), but ``PreviewFilter.resolve_output_port_id`` reads this
    # map to tell downstream wiring where to source each virtual output.
    for virtual_name, (port_fid, port_ch) in res.external_ports.items():
        if virtual_name in mapping:
            continue
        if port_fid != cue_fid:
            mapping[virtual_name] = f"{port_fid}:{port_ch}"

    # Pass 2 — clone the postprocess chain into the preview scene.
    #
    # Skip the compiler's standalone ``__CONST__`` filters for defaulted
    # canonicals: the matching PREVIEW_CONST from pass 1 covers the same
    # channel, and cloning both would leave fish with two filters driving
    # the same stream. Every clone's channel_links are rewritten so cue
    # filter references (``{cue_fid}:raw``) and standalone CONST references
    # (``{cue_fid}__CONST__{canonical}:value``) both route to the matching
    # PREVIEW_CONST.
    defaulted_const_ids = {f"{cue_fid}__CONST__{canonical}" for canonical in canonicals}
    for pp_src in res.postprocess_filters:
        if pp_src.filter_id in defaulted_const_ids:
            continue
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
    """Rewrite one strategy channel_link to point at a PREVIEW_CONST.

    Handles both forms of reference the compiler emits:

    * ``{cue_fid}:{raw}`` -- a direct cue-filter raw-channel read; replaced
      by the PREVIEW_CONST matching ``consolidation.canonical(raw)``.
    * ``{cue_fid}__CONST__{canonical}:value`` -- the compiler's standalone
      CONST for a defaulted canonical. In preview the standalone CONST is
      not cloned into the scene, so we redirect to the same canonical's
      PREVIEW_CONST.
    """
    if not source:
        return source
    const_marker = f"{cue_fid}__CONST__"
    if source.startswith(const_marker):
        rest = source[len(const_marker):]
        canonical, _, _ = rest.partition(":")
        const_id = canonical_to_const_id.get(canonical)
        return f"{const_id}:value" if const_id else source
    cue_prefix = f"{cue_fid}:"
    if source.startswith(cue_prefix):
        local = source[len(cue_prefix):]
        canonical = consolidation.canonical(local)
        const_id = canonical_to_const_id.get(canonical)
        return f"{const_id}:value" if const_id else source
    return source


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
        """Initialise the preview thread with its vfilter, channel map, tick rate and parent."""
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
        """Update the current playback timecode in seconds."""
        self._timecode = float(seconds)

    def set_playing(self, playing: bool) -> None:
        """Set whether the preview thread is actively emitting tick updates."""
        self._playing = bool(playing)

    def set_cue_index(self, index: int) -> None:
        """Select which cue index is evaluated on each tick."""
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
