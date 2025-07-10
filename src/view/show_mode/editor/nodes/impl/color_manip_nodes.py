from model.filter import DataType, Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.aggregating_filter_node import AggregatingFilterNode


class ColorMixerHSVNode(AggregatingFilterNode):
    nodeName = "Color Mixer HSV"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerAdditiveRGBNode(AggregatingFilterNode):
    nodeName = "Color Mixer Additive RGB"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerNormativeRGBNode(AggregatingFilterNode):
    nodeName = "Color Mixer Normative RGB"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerVFilterNode(AggregatingFilterNode):
    nodeName = "Color Mixer"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER)
