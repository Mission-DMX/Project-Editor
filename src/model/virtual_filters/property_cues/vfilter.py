"""Property-based cue virtual filter shell (WP9)."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from model.filter import DataType, Filter, FilterTypeEnumeration
from model.virtual_filters.cue_vfilter import PreviewFilter
from model.virtual_filters.property_cues.compiler import (
    CompileResult,
    compile_property_model,
)
from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel

if TYPE_CHECKING:
    from model import Scene

logger = getLogger(__name__)


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

    def _ensure_compiled(self) -> CompileResult:
        """Compile the model if needed and refresh ``self._out_data_types``."""
        if self._last_compile is None:
            self._last_compile = compile_property_model(
                self._property_model,
                cue_filter_id=self.filter_id,
                scene=self.scene,
                pos=self.pos,
            )
            self._out_data_types = {
                virtual_port: self._last_compile.channel_specs[virtual_port].data_type
                for virtual_port in self._last_compile.channel_specs
            }
        return self._last_compile

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
