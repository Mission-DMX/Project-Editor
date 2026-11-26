"""VFilter that mixes multiple color inputs into a single color output."""

from typing import override

from model import Filter, Scene
from model.filter import DataType, FilterTypeEnumeration, VirtualFilter


class ColorMixerVFilter(VirtualFilter):
    """VFilter that mixes multiple color inputs into a single color output using a fish color mixer filter."""

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        """Resolve the virtual output port to the port of the instantiated mixer filter."""
        return f"{self.filter_id}:{virtual_port_id}"

    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        """Instantiate the fish color mixer filter using the configured mixing method."""
        from model.filters.factory import construct_filter_instance

        method = self.filter_configurations.get("method")
        match method:
            case "hsv":
                f_type = FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV
            case "hsv_red_sat":
                f_type = FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV
            case "additive_rgb":
                f_type = FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB
            case "normative_rgb":
                f_type = FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATIVE_RGB
            case _:
                f_type = FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV
        mixer_filter = construct_filter_instance(
            scene=self.scene,
            filter_id=self.filter_id,
            filter_type=f_type,
            pos=self.pos,
            filter_configurations=self.filter_configurations.copy(),
            initial_parameters={"reduce_saturation_on_far_angles": "true"} if method == "hsv_red_sat" else {},
        )
        for k, v in self.channel_links.items():
            mixer_filter.channel_links[k] = v
        filter_list.append(mixer_filter)

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None) -> None:
        """Initialize the color mixer v-filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLOR_MIXER, pos=pos)

    @override
    def _rebuild_io(self) -> None:
        """Mirror the underlying colour-mixer's signature: N DT_COLOR inputs + one DT_COLOR ``value`` output.

        Input count comes from the ``input_count`` configuration (default ``"2"``) using the
        same semantics as :class:`model.filters.aggregating._AggregatingFilterBase`.
        """
        self._in_data_types = {}
        self._out_data_types = {"value": DataType.DT_COLOR}
        self._default_values = {}
        self._gui_update_keys = {}
        self._filter_configurations.setdefault("method", "hsv")
        self._filter_configurations.setdefault("input_count", "2")
        raw_count = self._filter_configurations.get("input_count", "2")
        try:
            count = int(raw_count)
        except ValueError:
            count = 0
            self._filter_configurations["input_count"] = "0"
        if count < 0:
            count = 0
        for i in range(count):
            name = str(i)
            self._in_data_types[name] = DataType.DT_COLOR
            self._default_values[name] = "0,0,0"
