"""Contains filter nodes for color manipulation."""
from typing import override

from model.filter import DataType, Filter, FilterTypeEnumeration
from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter
from view.show_mode.editor.nodes import FilterNode
from view.show_mode.editor.nodes.base.aggregating_filter_node import AggregatingFilterNode


class ColorMixerHSVNode(AggregatingFilterNode):
    """Node to mix colors based on their HSV representation."""

    nodeName = "Color Mixer HSV"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerAdditiveRGBNode(AggregatingFilterNode):
    """Node to mix colors based on their RGB representation using the additive algorithm."""

    nodeName = "Color Mixer Additive RGB"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerNormativeRGBNode(AggregatingFilterNode):
    """Node to mix colors based on their RGB representation using the normative algorithm."""

    nodeName = "Color Mixer Normative RGB"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerVFilterNode(AggregatingFilterNode):
    """Node to mix colors, using configurable virtual filter."""

    nodeName = "Color Mixer"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER)


class ColorDirectorVFilterNode(FilterNode):
    """Filter node for color director virtual filter."""

    nodeName = "Color Director"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize."""
        super().__init__(model, FilterTypeEnumeration.VFILTER_COLORDIRECTOR, name,
                         terminals={"time": {"io": "in"}, "time_scale": {"io": "in"}})

    @override
    def update_node_after_settings_changed(self) -> None:

        f = self.filter
        if not isinstance(f, ColordirectorVFilter):
            raise ValueError("Expected ColordirectorVFilter.")
        existing_outputs = self.outputs().keys()
        new_outputs = f.get_outputs()
        for output in new_outputs:
            if output not in existing_outputs:
                self.addOutput(output)
        for output in existing_outputs:
            if output not in new_outputs:
                self.removeTerminal(output)

