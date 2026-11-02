"""Dimmer Director filter (type 84).

Fans a 16bit dimmer input per group out to an X*Y*Z grid of 16bit outputs, modulated by
a pre-sampled effect curve shifted per axis and shaped by a dimmer response curve. See
``Docs/Editor/Filters/Filter_Types/effects.md`` for the fish-side specification.

The editor model owns the following, serialized through ``filter_configurations``:

* Groups, effect curves, dimmer curves: fish-native keys (``groups``, ``effect_curves``,
  ``dimmer_curves``) parsed back from the format accepted by fish.
* Editor-only sidecar keys: ``n_mix_global``, ``n_off_global``, ``*_icons`` (asset
  uuids), ``effect_curve_keyframes`` (``Cue`` keyframes per effect curve — the ground
  truth whenever the user is editing in the timeline), ``recalls`` and
  ``format_version``.

Effect-curve storage has two modes:

* **Keyframe mode** — the user edits a ``Cue`` with one ``DT_DOUBLE`` channel in a
  timeline widget. The ``samples`` list that fish actually consumes is a cache derived
  by resampling the cue at the fish tick rate (40 Hz, 25 ms per tick).
* **CSV-imported mode** — the user has imported a sample list from a .csv file; no
  keyframes exist. The config widget detects this by checking the model's
  ``is_csv_imported`` flag per curve and disables the timeline until the samples are
  cleared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QObject, Signal

from model.filter import DataType, Filter, FilterTypeEnumeration
from model.filter_data.cues.cue import Cue, KeyFrame, StateDouble
from model.filter_data.transfer_function import TransferFunction
from model.filters._channel_names import is_valid_channel_name, sanitize_channel_name
from model.filters.factory import register_filter
from model.media_assets.image import AbstractImageAsset
from model.media_assets.registry import get_asset_by_uuid

if TYPE_CHECKING:
    import proto.FilterMode_pb2
    from model import Scene

logger = getLogger(__name__)


_FORMAT_VERSION = 1
"""Serialized configuration format version written and understood by this editor."""

_TICK_PERIOD_MS = 25
"""Fish update tick period in milliseconds (40 Hz)."""

_DEFAULT_THRESHOLD = 0.1
_DEFAULT_WINDOW = 1
_MAX_RECALL_COUNT = 1024


class EffectCurveMode(Enum):
    """How fish advances an effect curve while it is active."""

    REPEAT = "REPEAT"
    TRIGGER = "TRIGGER"


class DimmerCurveType(Enum):
    """Response curve types supported by fish for the final dimmer shaping."""

    LIN = "LIN"
    SIG = "SIG"
    BEZIER = "BEZIER"


@dataclass
class DimmerGroup:
    """One group of fixtures laid out on an X*Y*Z grid."""

    name: str
    x: int = 1
    y: int = 1
    z: int = 1
    n_mix_group: int = 0
    n_off_group: int = 0
    phase_x: int = 0
    phase_y: int = 0
    phase_z: int = 0


class EffectCurve:
    """One pre-sampled effect curve that can be assigned to a group at runtime."""

    def __init__(self, name: str = "curve") -> None:
        """Initialize an empty REPEAT curve without samples, keyframes or icon."""
        self.name: str = name
        self.mode: EffectCurveMode = EffectCurveMode.REPEAT
        self.threshold: float = _DEFAULT_THRESHOLD
        self.window: int = _DEFAULT_WINDOW
        self.samples: list[float] = []
        self.cue: Cue | None = None
        self._icon_asset: AbstractImageAsset | str | None = None

    @property
    def icon_asset(self) -> AbstractImageAsset | None:
        """Resolve and cache the icon asset referenced by this curve."""
        if isinstance(self._icon_asset, str):
            resolved = get_asset_by_uuid(self._icon_asset)
            self._icon_asset = resolved if isinstance(resolved, AbstractImageAsset) else None
        return self._icon_asset if isinstance(self._icon_asset, AbstractImageAsset) else None

    @icon_asset.setter
    def icon_asset(self, asset: AbstractImageAsset | None) -> None:
        self._icon_asset = asset

    def icon_asset_uuid(self) -> str:
        """Return the serialized asset uuid or the empty string if no asset is configured."""
        if isinstance(self._icon_asset, AbstractImageAsset):
            return self._icon_asset.id
        if isinstance(self._icon_asset, str):
            return self._icon_asset
        return ""

    def is_csv_imported(self) -> bool:
        """True when samples exist without any backing keyframes (CSV-imported state)."""
        has_keyframes = self.cue is not None and len(self.cue._frames) > 0
        return not has_keyframes and len(self.samples) > 0


class DimmerCurve:
    """One response curve applied after the effect curve."""

    def __init__(self, name: str = "curve") -> None:
        """Initialize a LIN curve without parameters or icon."""
        self.name: str = name
        self.type: DimmerCurveType = DimmerCurveType.LIN
        self.params: list[float] = []
        self._icon_asset: AbstractImageAsset | str | None = None

    @property
    def icon_asset(self) -> AbstractImageAsset | None:
        """Resolve and cache the icon asset referenced by this curve."""
        if isinstance(self._icon_asset, str):
            resolved = get_asset_by_uuid(self._icon_asset)
            self._icon_asset = resolved if isinstance(resolved, AbstractImageAsset) else None
        return self._icon_asset if isinstance(self._icon_asset, AbstractImageAsset) else None

    @icon_asset.setter
    def icon_asset(self, asset: AbstractImageAsset | None) -> None:
        self._icon_asset = asset

    def icon_asset_uuid(self) -> str:
        """Return the serialized asset uuid or the empty string if no asset is configured."""
        if isinstance(self._icon_asset, AbstractImageAsset):
            return self._icon_asset.id
        if isinstance(self._icon_asset, str):
            return self._icon_asset
        return ""


@dataclass
class RecallEntry:
    """One recall storing an (effect curve, dimmer curve) selection per group."""

    selections: list[tuple[int, int]] = field(default_factory=list)


class _SignalProvider(QObject):
    """Wrap a Qt signal so the non-QObject filter model can emit configuration changes."""

    mapped_signal = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the signal provider."""
        super().__init__(parent)


def _format_float(value: float) -> str:
    """Format a float for serialization using the shortest round-trip representation."""
    return f"{value:g}"


def _sample_cue(cue: Cue) -> list[float]:
    """Resample a cue holding one DT_DOUBLE channel at the fish update tick rate.

    The samples list has as many entries as there are 25 ms ticks between 0.0 s and the
    last keyframe's timestamp (inclusive). An empty cue returns an empty sample list.
    """
    if cue is None or len(cue._frames) == 0:
        return []
    frames = sorted(cue._frames, key=lambda f: f.timestamp)
    duration_s = frames[-1].timestamp
    if duration_s <= 0.0:
        return [float(frames[0]._states[0]._value) if frames[0]._states else 0.0]
    tick_count = max(1, round(duration_s * 1000.0 / _TICK_PERIOD_MS))
    samples: list[float] = []
    for i in range(tick_count):
        t = (i * _TICK_PERIOD_MS) / 1000.0
        samples.append(_interpolate_at(frames, t))
    return samples


def _interpolate_at(frames: list[KeyFrame], t: float) -> float:
    """Linear interpolation between keyframes using their transfer-function markers.

    This is a minimal single-channel version of ``_value_at_time`` from
    ``property_cues/preview_runtime.py``: effect curves have exactly one DT_DOUBLE
    channel so the full-featured preview runtime (color handling, consolidation) is not
    needed here.
    """
    if not frames or not frames[0]._states:
        return 0.0
    if t <= frames[0].timestamp:
        return float(frames[0]._states[0]._value)
    if t >= frames[-1].timestamp:
        return float(frames[-1]._states[0]._value)
    prev = frames[0]
    nxt = frames[-1]
    for i in range(1, len(frames)):
        if frames[i].timestamp >= t:
            prev = frames[i - 1]
            nxt = frames[i]
            break
    if not prev._states or not nxt._states:
        return 0.0
    span = nxt.timestamp - prev.timestamp
    if span <= 0.0:
        return float(nxt._states[0]._value)
    rel = (t - prev.timestamp) / span
    from model.filter_data.cues.curves import value_at

    try:
        transition = TransferFunction(nxt._states[0]._transition_type)
    except ValueError:
        transition = TransferFunction.LINEAR
    return float(value_at(rel, prev._states[0], nxt._states[0], transition))


def _parse_int(value: str, default: int) -> int:
    """Parse an int, returning ``default`` on failure."""
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: str, default: float) -> float:
    """Parse a float, returning ``default`` on failure."""
    try:
        return float(value)
    except ValueError:
        return default


@register_filter(FilterTypeEnumeration.FILTER_DIMMER_DIRECTOR)
class DimmerDirectorFilter(Filter):
    """Editor-side model for ``filter_dimmer_director`` (type 84)."""

    CONFIGURATION_SUPPORTED = True

    def __init__(
        self,
        scene: Scene,
        filter_id: str,
        filter_type: int = FilterTypeEnumeration.FILTER_DIMMER_DIRECTOR,
        pos: tuple[int, int] | tuple[float, float] | None = None,
        filter_configurations: dict[str, str] | None = None,
        initial_parameters: dict[str, str] | None = None,
    ) -> None:
        """Initialize the filter and deserialize any provided configuration."""
        self._global_mixin_count: int = 0
        self._global_offset_count: int = 0
        self._groups: list[DimmerGroup] = []
        self._effect_curves: list[EffectCurve] = []
        self._dimmer_curves: list[DimmerCurve] = []
        self._recalls: list[RecallEntry] = []
        self._configuration_format_supported: bool = True
        self._dirty: bool = False

        self._active_effect_indices: list[int] = []
        self._active_dimmer_indices: list[int] = []
        self._group_paused_states: list[bool] = []

        self.configuration_changed = _SignalProvider()

        super().__init__(
            scene=scene,
            filter_id=filter_id,
            filter_type=int(filter_type),
            pos=pos,
            filter_configurations=filter_configurations,
            initial_parameters=initial_parameters,
        )
        self._deserialize_from_configuration()
        self._apply_io_from_state()
        self.configuration_changed.mapped_signal.connect(self._mark_dirty)
        self._register_feedback_callback()

    def _mark_dirty(self) -> None:
        """Flag the dataclass state as newer than ``_filter_configurations``.

        The ``filter_configurations`` property picks up this flag on the next external
        access and runs ``serialize_to_configuration()`` just-in-time.
        """
        self._dirty = True

    @property
    def filter_configurations(self) -> dict[str, str]:
        """Return the (possibly just-flushed) ``filter_configurations`` dict.

        If any dataclass state has changed since the last serialize, flush it to
        ``_filter_configurations`` before returning so the show-file writer sees the
        latest values. During show-file loading no edits occur, ``_dirty`` stays ``False``,
        and the loader can therefore populate ``_filter_configurations`` incrementally
        without the getter clobbering its writes.
        """
        if getattr(self, "_dirty", False):
            self.serialize_to_configuration()
            self._dirty = False
        return self._filter_configurations

    def _register_feedback_callback(self) -> None:
        """Subscribe this filter to its own fish ``update_parameter`` messages.

        Registration is best-effort — if the scene has no board configuration yet (e.g.
        during very early bootstrapping) the callback is skipped silently and the filter
        will fall back to the editor-only state without live feedback.
        """
        try:
            self.scene.board_configuration.register_filter_update_callback(
                self.scene, self.filter_id, self.handle_filter_feedback,
            )
        except (AttributeError, RuntimeError) as exc:
            logger.debug("Skipping feedback registration for %s: %s", self.filter_id, exc)

    # ------------------------------------------------------------------ I/O

    @override
    def _rebuild_io(self) -> None:
        """Framework hook — invoked by base ``Filter.__init__`` and by the show-file loader.

        The loader populates ``_filter_configurations`` by writing into the dict returned
        from this instance's property, then calls ``_rebuild_io()`` once the writes are
        complete (see ``controller/file/read.py:467``). We use that call to pull the
        just-populated dict into the dataclass state before rebuilding the I/O signature.
        For code paths that modify state directly through the model API (``add_group``,
        ``update_group``, …), the public helper :meth:`_apply_io_from_state` is called
        instead so the deserialize branch here is only exercised when the dict is
        authoritative.
        """
        # ``_dirty`` is not guaranteed to exist during the very first call that comes from
        # the base ``Filter.__init__`` (we initialise it just above super().__init__). The
        # getattr guards against that early call. Model state attributes are always set
        # before super().__init__ so ``_apply_io_from_state`` is safe.
        if getattr(self, "_filter_configurations", None):
            self._deserialize_from_configuration()
        self._apply_io_from_state()

    def _apply_io_from_state(self) -> None:
        """Derive input and output terminals from the current dataclass state."""
        self._in_data_types = {}
        self._out_data_types = {}
        self._default_values = {}
        self._gui_update_keys = {
            "active_effect": DataType.DT_DOUBLE,
            "active_dimmer": DataType.DT_DOUBLE,
            "pause_effect": DataType.DT_DOUBLE,
            "resume_effect": DataType.DT_DOUBLE,
        }
        for i in range(self._global_mixin_count):
            self._in_data_types[f"mixin_{i}"] = DataType.DT_16_BIT
        for i in range(self._global_offset_count):
            self._in_data_types[f"offset_{i}"] = DataType.DT_16_BIT
        for group in self._groups:
            name = sanitize_channel_name(group.name)
            self._in_data_types[name] = DataType.DT_16_BIT
            for j in range(group.n_mix_group):
                self._in_data_types[f"mixin_{name}_{j}"] = DataType.DT_16_BIT
            for l_ in range(group.n_off_group):
                self._in_data_types[f"offset_{name}_{l_}"] = DataType.DT_16_BIT
            for z in range(max(1, group.z)):
                for y in range(max(1, group.y)):
                    for x in range(max(1, group.x)):
                        self._out_data_types[f"{name}_{x}_{y}_{z}"] = DataType.DT_16_BIT

    # ---------------------------------------------------------------- state

    @property
    def configuration_format_supported(self) -> bool:
        """Whether the last-deserialized configuration uses a supported format version."""
        return self._configuration_format_supported

    @property
    def global_mixin_count(self) -> int:
        """Number of global ``mixin_<i>`` input channels."""
        return self._global_mixin_count

    @global_mixin_count.setter
    def global_mixin_count(self, value: int) -> None:
        value = max(0, int(value))
        if value == self._global_mixin_count:
            return
        self._global_mixin_count = value
        self._apply_io_from_state()
        self.configuration_changed.mapped_signal.emit()

    @property
    def global_offset_count(self) -> int:
        """Number of global ``offset_<i>`` input channels."""
        return self._global_offset_count

    @global_offset_count.setter
    def global_offset_count(self, value: int) -> None:
        value = max(0, int(value))
        if value == self._global_offset_count:
            return
        self._global_offset_count = value
        self._apply_io_from_state()
        self.configuration_changed.mapped_signal.emit()

    @property
    def groups(self) -> list[DimmerGroup]:
        """A shallow copy of the groups list. Mutate structural changes via the add/remove helpers."""
        return list(self._groups)

    @property
    def effect_curves(self) -> list[EffectCurve]:
        """A shallow copy of the effect curves list."""
        return list(self._effect_curves)

    @property
    def dimmer_curves(self) -> list[DimmerCurve]:
        """A shallow copy of the dimmer curves list."""
        return list(self._dimmer_curves)

    @property
    def recalls(self) -> list[RecallEntry]:
        """A shallow copy of the recalls list."""
        return list(self._recalls)

    def add_group(self, name: str) -> DimmerGroup | None:
        """Append a new group with the provided name. Returns None on name validation failure."""
        if not is_valid_channel_name(name) or any(g.name == name for g in self._groups):
            return None
        group = DimmerGroup(name=name)
        self._groups.append(group)
        for recall in self._recalls:
            recall.selections.append((0, 0))
        self._apply_io_from_state()
        self.configuration_changed.mapped_signal.emit()
        return group

    def remove_group(self, index: int) -> bool:
        """Remove the group at ``index`` and shrink every recall accordingly."""
        if not 0 <= index < len(self._groups):
            return False
        self._groups.pop(index)
        for recall in self._recalls:
            if index < len(recall.selections):
                recall.selections.pop(index)
        if index < len(self._active_effect_indices):
            self._active_effect_indices.pop(index)
        if index < len(self._active_dimmer_indices):
            self._active_dimmer_indices.pop(index)
        if index < len(self._group_paused_states):
            self._group_paused_states.pop(index)
        self._apply_io_from_state()
        self.configuration_changed.mapped_signal.emit()
        return True

    def update_group(self, index: int, group: DimmerGroup) -> bool:
        """Replace the group at ``index`` with ``group``. Returns False on invalid input."""
        if not 0 <= index < len(self._groups):
            return False
        if not is_valid_channel_name(group.name):
            return False
        if any(i != index and other.name == group.name for i, other in enumerate(self._groups)):
            return False
        self._groups[index] = group
        self._apply_io_from_state()
        self.configuration_changed.mapped_signal.emit()
        return True

    def add_effect_curve(self, name: str = "effect") -> EffectCurve:
        """Append a new empty effect curve."""
        curve = EffectCurve(name=name)
        self._effect_curves.append(curve)
        self.configuration_changed.mapped_signal.emit()
        return curve

    def remove_effect_curve(self, index: int) -> bool:
        """Remove the effect curve at ``index`` and clamp recalls that referenced it."""
        if not 0 <= index < len(self._effect_curves):
            return False
        self._effect_curves.pop(index)
        for recall in self._recalls:
            for i, (eff, dim) in enumerate(recall.selections):
                if eff >= index and eff > 0:
                    recall.selections[i] = (max(0, eff - 1), dim)
        self.configuration_changed.mapped_signal.emit()
        return True

    def add_dimmer_curve(self, name: str = "dimmer") -> DimmerCurve:
        """Append a new LIN dimmer curve."""
        curve = DimmerCurve(name=name)
        self._dimmer_curves.append(curve)
        self.configuration_changed.mapped_signal.emit()
        return curve

    def remove_dimmer_curve(self, index: int) -> bool:
        """Remove the dimmer curve at ``index`` and clamp recalls that referenced it."""
        if not 0 <= index < len(self._dimmer_curves):
            return False
        self._dimmer_curves.pop(index)
        for recall in self._recalls:
            for i, (eff, dim) in enumerate(recall.selections):
                if dim >= index and dim > 0:
                    recall.selections[i] = (eff, max(0, dim - 1))
        self.configuration_changed.mapped_signal.emit()
        return True

    def add_recall(self) -> RecallEntry:
        """Add a recall selecting (0, 0) for every group."""
        recall = RecallEntry(selections=[(0, 0) for _ in self._groups])
        self._recalls.append(recall)
        self.configuration_changed.mapped_signal.emit()
        return recall

    def remove_recall(self, index: int) -> bool:
        """Remove the recall at ``index``."""
        if not 0 <= index < len(self._recalls):
            return False
        self._recalls.pop(index)
        self.configuration_changed.mapped_signal.emit()
        return True

    def set_recall_selection(self, recall_index: int, group_index: int, effect: int, dimmer: int) -> bool:
        """Store an (effect, dimmer) selection for a group within a recall."""
        if not 0 <= recall_index < len(self._recalls):
            return False
        if not 0 <= group_index < len(self._groups):
            return False
        recall = self._recalls[recall_index]
        while len(recall.selections) <= group_index:
            recall.selections.append((0, 0))
        effect = max(0, min(effect, max(0, len(self._effect_curves) - 1)))
        dimmer = max(0, min(dimmer, max(0, len(self._dimmer_curves) - 1)))
        recall.selections[group_index] = (effect, dimmer)
        self.configuration_changed.mapped_signal.emit()
        return True

    # -------------------------------------------------------------- samples

    def resample_effect_curve(self, index: int) -> None:
        """Rebuild the ``samples`` cache of an effect curve from its keyframes."""
        if not 0 <= index < len(self._effect_curves):
            return
        curve = self._effect_curves[index]
        if curve.cue is not None and len(curve.cue._frames) > 0:
            curve.samples = _sample_cue(curve.cue)
            self.configuration_changed.mapped_signal.emit()

    def clear_effect_curve_samples(self, index: int) -> bool:
        """Drop the CSV-imported samples of an effect curve so keyframe editing is re-enabled."""
        if not 0 <= index < len(self._effect_curves):
            return False
        curve = self._effect_curves[index]
        curve.samples = []
        if curve.cue is None:
            curve.cue = Cue()
            curve.cue.add_channel("value", DataType.DT_DOUBLE)
        self.configuration_changed.mapped_signal.emit()
        return True

    def import_effect_curve_samples(self, index: int, samples: list[float]) -> bool:
        """Replace an effect curve's samples with the ones from a CSV import and drop keyframes."""
        if not 0 <= index < len(self._effect_curves):
            return False
        curve = self._effect_curves[index]
        curve.samples = [max(-1.0, min(1.0, float(v))) for v in samples]
        curve.cue = None
        self.configuration_changed.mapped_signal.emit()
        return True

    # ------------------------------------------------------- update messages

    def get_update_msg_for_effect_change(self, group: str, idx: int) -> tuple[str, str]:
        """Build the ``(target, value)`` tuple that switches a group's active effect curve."""
        return f"{self.filter_id}:active_effect", f"{sanitize_channel_name(group)}:{int(idx)}"

    def get_update_msg_for_dimmer_change(self, group: str, idx: int) -> tuple[str, str]:
        """Build the ``(target, value)`` tuple that switches a group's active dimmer curve."""
        return f"{self.filter_id}:active_dimmer", f"{sanitize_channel_name(group)}:{int(idx)}"

    def get_update_msg_for_pause(self, group: str) -> tuple[str, str]:
        """Build the ``(target, value)`` tuple that pauses a group's effect curve."""
        return f"{self.filter_id}:pause_effect", sanitize_channel_name(group)

    def get_update_msg_for_resume(self, group: str) -> tuple[str, str]:
        """Build the ``(target, value)`` tuple that resumes a group's effect curve."""
        return f"{self.filter_id}:resume_effect", sanitize_channel_name(group)

    # ---------------------------------------------------------- fish feedback

    def handle_filter_feedback(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Parse an ``update_parameter`` message from fish and update active-curve state."""
        if param.filter_id != self.filter_id:
            return
        key = param.parameter_key
        value = param.parameter_value
        if key == "effect_state":
            self._parse_effect_state(value)
        elif key == "dimmer_state":
            self._parse_dimmer_state(value)

    def _parse_effect_state(self, value: str) -> None:
        parts = value.split(":")
        if len(parts) < 3:
            return
        group_name = parts[0]
        try:
            idx = int(parts[1])
        except ValueError:
            return
        running = parts[2] == "running"
        group_index = self._group_index_by_name(group_name)
        if group_index is None:
            return
        self._ensure_feedback_lists()
        changed = False
        if self._active_effect_indices[group_index] != idx:
            self._active_effect_indices[group_index] = idx
            changed = True
        if self._group_paused_states[group_index] != (not running):
            self._group_paused_states[group_index] = not running
            changed = True
        if changed:
            self.configuration_changed.mapped_signal.emit()

    def _parse_dimmer_state(self, value: str) -> None:
        parts = value.split(":")
        if len(parts) < 2:
            return
        group_name = parts[0]
        try:
            idx = int(parts[1])
        except ValueError:
            return
        group_index = self._group_index_by_name(group_name)
        if group_index is None:
            return
        self._ensure_feedback_lists()
        if self._active_dimmer_indices[group_index] != idx:
            self._active_dimmer_indices[group_index] = idx
            self.configuration_changed.mapped_signal.emit()

    def _group_index_by_name(self, name: str) -> int | None:
        for i, g in enumerate(self._groups):
            if g.name == name:
                return i
        return None

    def _ensure_feedback_lists(self) -> None:
        count = len(self._groups)
        while len(self._active_effect_indices) < count:
            self._active_effect_indices.append(0)
        while len(self._active_dimmer_indices) < count:
            self._active_dimmer_indices.append(0)
        while len(self._group_paused_states) < count:
            self._group_paused_states.append(False)

    def get_active_effect_indices(self) -> list[int]:
        """Return a copy of the per-group active effect-curve indices (0-filled when unknown)."""
        self._ensure_feedback_lists()
        return list(self._active_effect_indices)

    def get_active_dimmer_indices(self) -> list[int]:
        """Return a copy of the per-group active dimmer-curve indices."""
        self._ensure_feedback_lists()
        return list(self._active_dimmer_indices)

    def get_group_paused_states(self) -> list[bool]:
        """Return a copy of the per-group paused flags."""
        self._ensure_feedback_lists()
        return list(self._group_paused_states)

    # ----------------------------------------------------------- serializing

    def _deserialize_from_configuration(self) -> None:
        """Load every state field from ``filter_configurations``."""
        format_version = self._read_format_version()
        self._configuration_format_supported = format_version == _FORMAT_VERSION
        if not self._configuration_format_supported:
            logger.warning(
                "Ignoring the dimmer director configuration of '%s' because of its unsupported format version %r.",
                self.filter_id,
                self._filter_configurations.get("format_version"),
            )
            return
        self._global_mixin_count = _parse_int(self._filter_configurations.get("n_mix_global", "0"), 0)
        self._global_offset_count = _parse_int(self._filter_configurations.get("n_off_global", "0"), 0)
        self._deserialize_groups()
        self._deserialize_effect_curves()
        self._deserialize_dimmer_curves()
        self._deserialize_recalls()

    def _read_format_version(self) -> int | None:
        version_str = self._filter_configurations.get("format_version", "")
        if len(version_str) == 0:
            return _FORMAT_VERSION
        try:
            return int(version_str)
        except ValueError:
            return None

    def _deserialize_groups(self) -> None:
        self._groups.clear()
        raw = self._filter_configurations.get("groups", "")
        if not raw:
            return
        for group_def in raw.split(";"):
            if not group_def:
                continue
            parts = group_def.split(":")
            if len(parts) < 9:
                logger.warning("Skipping malformed group definition: %r", group_def)
                continue
            name = sanitize_channel_name(parts[0])
            if not is_valid_channel_name(name):
                logger.warning("Skipping group with invalid name: %r", parts[0])
                continue
            try:
                group = DimmerGroup(
                    name=name,
                    x=max(1, int(parts[1])),
                    y=max(1, int(parts[2])),
                    z=max(1, int(parts[3])),
                    n_mix_group=max(0, int(parts[4])),
                    n_off_group=max(0, int(parts[5])),
                    phase_x=int(parts[6]),
                    phase_y=int(parts[7]),
                    phase_z=int(parts[8]),
                )
            except ValueError:
                logger.warning("Skipping group with non-integer fields: %r", group_def)
                continue
            self._groups.append(group)

    def _deserialize_effect_curves(self) -> None:
        self._effect_curves.clear()
        raw = self._filter_configurations.get("effect_curves", "")
        icons_raw = self._filter_configurations.get("effect_curve_icons", "")
        keyframes_raw = self._filter_configurations.get("effect_curve_keyframes", "")
        icons = icons_raw.split(";") if icons_raw else []
        # ``~`` separates the serialized cues of different curves; it is not used anywhere
        # in Cue.format_cue (which uses ``:``, ``|``, ``#``, ``&``, ``@``, ``,``).
        keyframes = keyframes_raw.split("~") if keyframes_raw else []
        if not raw:
            return
        for i, curve_def in enumerate(raw.split(";")):
            if not curve_def:
                continue
            parts = curve_def.split(":")
            if len(parts) < 5:
                logger.warning("Skipping malformed effect curve: %r", curve_def)
                continue
            name = parts[0]
            try:
                mode = EffectCurveMode(parts[1])
            except ValueError:
                mode = EffectCurveMode.REPEAT
            threshold = _parse_float(parts[2], _DEFAULT_THRESHOLD)
            window = max(1, _parse_int(parts[3], _DEFAULT_WINDOW))
            samples_str = ":".join(parts[4:])
            samples: list[float] = []
            if samples_str:
                for s in samples_str.split(","):
                    if not s:
                        continue
                    samples.append(max(-1.0, min(1.0, _parse_float(s, 0.0))))
            curve = EffectCurve(name=name)
            curve.mode = mode
            curve.threshold = threshold
            curve.window = window
            curve.samples = samples
            if i < len(icons) and icons[i]:
                curve._icon_asset = icons[i]
            if i < len(keyframes) and keyframes[i]:
                cue = Cue()
                cue.add_channel("value", DataType.DT_DOUBLE)
                cue.from_string_definition(keyframes[i])
                curve.cue = cue
            self._effect_curves.append(curve)

    def _deserialize_dimmer_curves(self) -> None:
        self._dimmer_curves.clear()
        raw = self._filter_configurations.get("dimmer_curves", "")
        icons_raw = self._filter_configurations.get("dimmer_curve_icons", "")
        icons = icons_raw.split(";") if icons_raw else []
        if not raw:
            return
        for i, curve_def in enumerate(raw.split(";")):
            if not curve_def:
                continue
            parts = curve_def.split(":")
            if len(parts) < 2:
                logger.warning("Skipping malformed dimmer curve: %r", curve_def)
                continue
            name = parts[0]
            try:
                curve_type = DimmerCurveType(parts[1])
            except ValueError:
                curve_type = DimmerCurveType.LIN
            params: list[float] = []
            if len(parts) >= 3 and parts[2]:
                for p in parts[2].split(","):
                    if not p:
                        continue
                    params.append(_parse_float(p, 0.0))
            curve = DimmerCurve(name=name)
            curve.type = curve_type
            curve.params = params
            if i < len(icons) and icons[i]:
                curve._icon_asset = icons[i]
            self._dimmer_curves.append(curve)

    def _deserialize_recalls(self) -> None:
        self._recalls.clear()
        raw = self._filter_configurations.get("recalls", "")
        if not raw:
            return
        for recall_def in raw.split(";"):
            if not recall_def:
                continue
            selections: list[tuple[int, int]] = []
            for pair in recall_def.split(","):
                if not pair:
                    continue
                parts = pair.split("/")
                if len(parts) != 2:
                    continue
                try:
                    selections.append((int(parts[0]), int(parts[1])))
                except ValueError:
                    selections.append((0, 0))
            self._recalls.append(RecallEntry(selections=selections))

    def serialize_to_configuration(self) -> None:
        """Write every state field back into ``filter_configurations``.

        Called just before the show file is persisted or transmitted. If the loaded
        configuration used an unsupported format version, the stored data is preserved
        verbatim instead of being overwritten by the empty model.
        """
        if not self._configuration_format_supported:
            return
        self._filter_configurations["format_version"] = str(_FORMAT_VERSION)
        self._filter_configurations["n_mix_global"] = str(self._global_mixin_count)
        self._filter_configurations["n_off_global"] = str(self._global_offset_count)
        self._filter_configurations["groups"] = ";".join(
            ":".join(
                [
                    sanitize_channel_name(g.name),
                    str(g.x),
                    str(g.y),
                    str(g.z),
                    str(g.n_mix_group),
                    str(g.n_off_group),
                    str(g.phase_x),
                    str(g.phase_y),
                    str(g.phase_z),
                ],
            )
            for g in self._groups
        )
        effect_strs: list[str] = []
        effect_icons: list[str] = []
        effect_keyframes: list[str] = []
        for curve in self._effect_curves:
            samples_str = ",".join(_format_float(s) for s in curve.samples)
            effect_strs.append(
                ":".join(
                    [
                        curve.name,
                        curve.mode.value,
                        _format_float(curve.threshold),
                        str(curve.window),
                        samples_str,
                    ],
                ),
            )
            effect_icons.append(curve.icon_asset_uuid())
            effect_keyframes.append(curve.cue.format_cue() if curve.cue is not None else "")
        self._filter_configurations["effect_curves"] = ";".join(effect_strs)
        self._filter_configurations["effect_curve_icons"] = ";".join(effect_icons)
        self._filter_configurations["effect_curve_keyframes"] = "~".join(effect_keyframes)

        dimmer_strs: list[str] = []
        dimmer_icons: list[str] = []
        for curve in self._dimmer_curves:
            params_str = ",".join(_format_float(p) for p in curve.params)
            dimmer_strs.append(f"{curve.name}:{curve.type.value}:{params_str}")
            dimmer_icons.append(curve.icon_asset_uuid())
        self._filter_configurations["dimmer_curves"] = ";".join(dimmer_strs)
        self._filter_configurations["dimmer_curve_icons"] = ";".join(dimmer_icons)

        self._filter_configurations["recalls"] = ";".join(
            ",".join(f"{eff}/{dim}" for eff, dim in r.selections) for r in self._recalls
        )
