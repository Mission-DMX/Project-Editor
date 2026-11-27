"""Property-based cue virtual filter shell."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from model.filter import DataType, Filter, FilterTypeEnumeration
from model.filters._channel_names import sanitize_channel_name
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

    S5: raw channels that only exist to feed post-processing filters (such as
    ``strobefreq``, ``duty_cycle``, ``pan_value``, ``tilt_curvesel``) are
    identified by their :attr:`ChannelSpec.exposed_locally` flag instead of
    the historic ``INTERNAL_LOCAL_NAMES`` lookup. The post-processed outputs
    they drive (``pan``, ``tilt`` -- 16-bit; ``brightness`` already shares a
    name with its raw counterpart since the strobe generator preserves the
    float type) are still synthesised via :func:`synthesized_output`. Order
    follows :func:`channel_sort_key`.
    """
    full: dict[str, object] = {}
    for name, spec in channel_specs.items():
        prefix, _, local = name.partition("__")
        syn = synthesized_output(local)
        if syn is not None:
            syn_local, syn_type = syn
            full.setdefault(f"{prefix}__{syn_local}", syn_type)
        # ``exposed_locally`` defaults to ``True`` so specs produced by
        # older code paths (defaulted CONST channels, headless unit-test
        # stubs) still surface on the node.
        if not getattr(spec, "exposed_locally", True):
            continue
        # Belt-and-braces fallback for callers that didn't thread the flag
        # through: keep the historic internal-local-names check so a legacy
        # spec dict still hides the raw channels.
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
        """Initialise the vfilter with its scene, id and optional canvas position."""
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
        """Return the underlying property-cue model backing this vfilter."""
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
        """Compile the model if needed and refresh ``self._out_data_types``.

        L14 + S4: a short-lived :class:`BoardFixtureInfo` memoises every
        per-fixture capability / wheel / segment lookup for the duration of
        the compile so repeated references to the same fixture only pay the
        board-lookup cost once. The preset library is cached module-wide so
        this call is effectively free when nothing changed on disk since the
        last compile.
        """
        if self._last_compile is None:
            from model.virtual_filters.property_cues.fixture_info import BoardFixtureInfo
            from model.virtual_filters.property_cues.presets import load_preset_library
            name_map = self._build_fixture_name_map()
            scene = getattr(self, "scene", None)
            board = getattr(scene, "board_configuration", None) if scene is not None else None
            info = BoardFixtureInfo(board)
            self._last_compile = compile_property_model(
                self._property_model,
                cue_filter_id=self.filter_id,
                scene=self.scene,
                pos=self.pos,
                preset_library=load_preset_library(),
                name_resolver=lambda fid: name_map.get(fid, fid),
                capability_lookup=lambda fid, _info=info: self._capabilities_or_all_enabled(_info, fid),
                gobo_wheel_count_lookup=info.gobo_wheels,
                beam_sub_capabilities_lookup=info.beam_parts,
                color_segment_count_lookup=info.color_segments,
            )
            self._out_data_types = _user_facing_outputs(self._last_compile.channel_specs)
        return self._last_compile

    def _capabilities_or_all_enabled(self, info, fixture_id: str) -> set[str]:  # noqa: ANN001
        """Return the fixture's physical capabilities, or every enabled one if unknown.

        Falls back to the model's enabled capability set when the fixture
        can't be located so headless tests still see output terminals for
        every capability they ticked.
        """
        caps = info.capabilities(fixture_id)
        if caps:
            return caps
        return {cap.value for cap in self._property_model.fixture_selection.enabled_capabilities}

    def _find_fixture(self, fixture_id: str):  # noqa: ANN202 — UsedFixture lazy import
        """Compatibility shim: delegate to a transient :class:`BoardFixtureInfo`.

        Retained for the small number of callers (tests, external integrations)
        that still reach for ``_find_fixture`` directly. Production code paths
        go through :class:`BoardFixtureInfo` via :meth:`_ensure_compiled`.
        """
        from model.virtual_filters.property_cues.fixture_info import BoardFixtureInfo
        scene = getattr(self, "scene", None)
        board = getattr(scene, "board_configuration", None) if scene is not None else None
        return BoardFixtureInfo(board)._fixture(fixture_id)

    def _build_fixture_name_map(self) -> dict[str, str]:
        """Build ``{fixture_id: display_name}`` with collision-safe suffixes.

        Collisions are detected AFTER running the stage name through the same
        sanitiser the compiler applies. Two fixtures named "MH 1" and "MH-1"
        both sanitise to "MH_1" — without post-sanitisation dedup, the second
        fixture's output ports would silently replace the first. Each colliding
        fixture gets an 8-character hex tail from its UUID so the resulting
        output port names remain distinct and deterministic across show reloads.
        Fixtures whose sanitised name is already unique keep the bare name.
        If the board is detached (tests, headless) the map is empty and the
        resolver falls back to the raw id.
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
            sanitized = sanitize_channel_name(name).rstrip("_")
            counts[sanitized] = counts.get(sanitized, 0) + 1
        result: dict[str, str] = {}
        for fid, name in bases.items():
            sanitized = sanitize_channel_name(name).rstrip("_")
            if counts[sanitized] > 1:
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
            # In preview mode the live preview replaces the native cue filter
            # with a set of constants driven by the preview runtime thread.
            from model.virtual_filters.property_cues.preview_runtime import (
                build_preview_filters,
            )
            mapping = build_preview_filters(self, self.scene, filter_list)
            self._channel_mapping = mapping
            return
        res = self._ensure_compiled()
        native = Filter(self.scene, self.filter_id,
                        FilterTypeEnumeration.FILTER_TYPE_CUES, self.pos)
        # ``res.native_model.get_as_configuration()`` fills the cue-specific
        # ``cuelist`` / ``mapping`` / ``end_handling`` / ``default_cue`` /
        # ``persistence`` entries. Everything else -- including the user's
        # ``time`` / ``time_scale`` channel_links and the gui_update_keys
        # fish needs to accept the configuration -- has to come from the
        # vfilter itself; the editor-only ``cues-prop-data`` blob is left
        # out so fish doesn't see it.
        native.filter_configurations.update(res.native_model.get_as_configuration())
        native.channel_links.update(self.channel_links)
        native.gui_update_keys.update(self.gui_update_keys)
        native.initial_parameters.update(self.initial_parameters)
        native.in_data_types.update(self.in_data_types)
        native.default_values.update(self.default_values)
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
