"""Property-based cue virtual filter shell (WP9)."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from model.filter import DataType, Filter, FilterTypeEnumeration
from model.virtual_filters.cue_vfilter import PreviewFilter
from model.virtual_filters.property_cues._channel_ordering import (
    INTERNAL_LOCAL_NAMES,
    channel_sort_key,
    synthesized_output,
)
from model.virtual_filters.property_cues.compiler import (
    CompileResult,
    compile_property_model,
)
from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel

if TYPE_CHECKING:
    from model import Scene

logger = getLogger(__name__)


def _user_facing_outputs(channel_specs: dict) -> dict:
    """Return ``{name: DataType}`` for the output terminals the node should expose.

    Hides the raw channels that only exist to feed post-processing filters
    (``strobefreq``, ``duty_cycle``, ``pan_value``, ``pan_curvesel``,
    ``tilt_value``, ``tilt_curvesel``) and synthesises the post-processed
    outputs they drive (``pan``, ``tilt`` -- 16-bit; ``brightness`` already
    shares a name with its raw counterpart since the strobe generator preserves
    the float type). Order follows :func:`channel_sort_key`.
    """
    full: dict[str, object] = {}
    for name, spec in channel_specs.items():
        prefix, _, local = name.partition("__")
        syn = synthesized_output(local)
        if syn is not None:
            syn_local, syn_type = syn
            full.setdefault(f"{prefix}__{syn_local}", syn_type)
        if local in INTERNAL_LOCAL_NAMES:
            continue
        full[name] = spec.data_type
    return {name: full[name] for name in sorted(full.keys(), key=channel_sort_key)}


class PropertyBasedCueFilter(PreviewFilter):
    """Virtual filter wrapping :class:`PropertyCueFilterModel`.

    On elaboration it compiles the model into a native cue filter plus an
    optional post-processing chain and exposes the compiled port map through
    :meth:`resolve_output_port_id`.
    """

    def __init__(self, scene: Scene, filter_id: str,
                 pos: tuple[int, int] | tuple[float, float] | None = None) -> None:
        super().__init__(
            scene, filter_id,
            FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES,
            FilterTypeEnumeration.FILTER_TYPE_CUES,
            pos=pos,
        )
        self._property_model: PropertyCueFilterModel = PropertyCueFilterModel()
        self._last_compile: CompileResult | None = None

    @property
    def property_model(self) -> PropertyCueFilterModel:
        return self._property_model

    @override
    def _rebuild_io(self) -> None:
        self._in_data_types = {
            "time": DataType.DT_DOUBLE,
            "time_scale": DataType.DT_DOUBLE,
        }
        self._default_values = {"time_scale": "1.0"}
        self._gui_update_keys = {
            "run_mode": ["play", "pause", "to_next_cue", "stop"],
            "run_cue": DataType.DT_16_BIT,
            "next_cue": DataType.DT_16_BIT,
        }
        self._filter_configurations.setdefault("cues-prop-data", "")
        self._out_data_types = {}
        # Repopulate from the current property model so the filter node knows
        # which output terminals to show. ``Filter.__init__`` calls this hook
        # before the subclass has set up ``_property_model``; the getattr
        # guard skips the compile on that first pre-init call.
        model = getattr(self, "_property_model", None)
        if model is None:
            return
        if not model.cues and not model.fixture_selection.entries:
            return
        self._last_compile = None
        try:
            self._ensure_compiled()
        except (ValueError, KeyError, AttributeError) as exc:
            logger.warning("Failed to compile property model during I/O refresh: %s", exc)

    def _ensure_compiled(self) -> CompileResult:
        """Compile the model if needed and refresh ``self._out_data_types``."""
        if self._last_compile is None:
            name_map = self._build_fixture_name_map()
            self._last_compile = compile_property_model(
                self._property_model,
                cue_filter_id=self.filter_id,
                scene=self.scene,
                pos=self.pos,
                name_resolver=lambda fid: name_map.get(fid, fid),
                capability_lookup=self._capability_lookup,
                gobo_wheel_count_lookup=self._gobo_wheel_count_lookup,
                beam_sub_capabilities_lookup=self._beam_sub_capabilities_lookup,
            )
            self._out_data_types = _user_facing_outputs(self._last_compile.channel_specs)
        return self._last_compile

    def _find_fixture(self, fixture_id: str):  # noqa: ANN202 — UsedFixture lazy import
        scene = getattr(self, "scene", None)
        board = getattr(scene, "board_configuration", None) if scene is not None else None
        if board is None:
            return None
        for fixture in getattr(board, "fixtures", []) or []:
            if str(getattr(fixture, "uuid", "")) == fixture_id:
                return fixture
        return None

    def _capability_lookup(self, fixture_id: str) -> set[str]:
        """Return the capabilities the fixture actually supports (as string values)."""
        fixture = self._find_fixture(fixture_id)
        if fixture is None:
            # Unknown fixture: permit every enabled capability so the user still
            # sees output terminals.
            return {cap.value for cap in self._property_model.fixture_selection.enabled_capabilities}
        from model.virtual_filters.property_cues.capability_discovery import discover_capabilities
        return {cap.value for cap in discover_capabilities([fixture])}

    def _gobo_wheel_count_lookup(self, fixture_id: str) -> int:
        """Return the number of gobo wheels on the fixture (0 if none)."""
        fixture = self._find_fixture(fixture_id)
        if fixture is None:
            return 1
        from model.virtual_filters.property_cues.capability_discovery import gobo_wheels_of
        return len(gobo_wheels_of(fixture))

    def _beam_sub_capabilities_lookup(self, fixture_id: str) -> set[str]:
        """Return the beam sub-capabilities (``"zoom"``, ``"iris"``, ``"prism"``) the fixture has."""
        fixture = self._find_fixture(fixture_id)
        if fixture is None:
            return {"zoom", "iris", "prism"}
        from model.virtual_filters.property_cues.capability_discovery import beam_sub_capabilities
        return beam_sub_capabilities(fixture)

    def _build_fixture_name_map(self) -> dict[str, str]:
        """Build ``{fixture_id: display_name}`` with collision-safe suffixes.

        When several fixtures share the same stage name (e.g. two "Hero Spot"
        instances), each gets an 8-character hex tail from its UUID appended
        so the resulting output port names remain distinct and deterministic
        across show reloads. Fixtures whose name is already unique keep the
        bare name. If the board is detached (tests, headless) the map is
        empty and the resolver falls back to the raw id.
        """
        scene = getattr(self, "scene", None)
        board = getattr(scene, "board_configuration", None) if scene is not None else None
        if board is None:
            return {}
        bases: dict[str, str] = {}
        for fixture in getattr(board, "fixtures", []) or []:
            fid = str(getattr(fixture, "uuid", ""))
            if not fid:
                continue
            bases[fid] = (
                getattr(fixture, "name_on_stage", None)
                or getattr(fixture, "name", None)
                or fid
            )
        counts: dict[str, int] = {}
        for name in bases.values():
            counts[name] = counts.get(name, 0) + 1
        result: dict[str, str] = {}
        for fid, name in bases.items():
            if counts[name] > 1:
                result[fid] = f"{name}_{fid.replace('-', '')[:8]}"
            else:
                result[fid] = name
        return result

    def invalidate_compile_cache(self) -> None:
        """Drop the cached :class:`CompileResult`; next call recompiles."""
        self._last_compile = None

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        if self.in_preview_mode:
            return super().resolve_output_port_id(virtual_port_id)
        res = self._ensure_compiled()
        port = res.external_ports.get(virtual_port_id)
        if port is None:
            return None
        return f"{port[0]}:{port[1]}"

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        if self.in_preview_mode:
            # WP12: the live preview replaces the native cue filter with a set
            # of constants driven by the preview runtime thread.
            from model.virtual_filters.property_cues.preview_runtime import (
                build_preview_filters,
            )
            mapping = build_preview_filters(self, self.scene, filter_list)
            self._channel_mapping = mapping
            return
        res = self._ensure_compiled()
        native = Filter(self.scene, self.filter_id,
                        FilterTypeEnumeration.FILTER_TYPE_CUES, self.pos)
        native.filter_configurations.update(res.native_model.get_as_configuration())
        filter_list.append(native)
        filter_list.extend(res.postprocess_filters)

    @override
    def serialize(self) -> None:
        self._filter_configurations["cues-prop-data"] = self._property_model.to_json_str()

    @override
    def deserialize(self) -> None:
        raw = self._filter_configurations.get("cues-prop-data", "")
        # Mutate in place -- UI widgets cache a reference to this model and must
        # observe the loaded data without reinstalling their bindings.
        self._property_model.load_from_json_str(raw)
        self._last_compile = None
        self._rebuild_io()
