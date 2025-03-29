# coding=utf-8
from model.filter import DataType, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.aggregating_filter_node import AggregatingFilterNode


class ColorMixerHSVNode(AggregatingFilterNode):
    nodeName = "Color Mixer HSV"

    def __init__(self, model, name):
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerAdditiveRGBNode(AggregatingFilterNode):
    nodeName = "Color Mixer Additive RGB"

    def __init__(self, model, name):
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerNormativeRGBNode(AggregatingFilterNode):
    nodeName = "Color Mixer Normative RGB"

    def __init__(self, model, name):
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)


class ColorMixerVFilterNode(AggregatingFilterNode):
    nodeName = "Color Mixer"

    def __init__(self, model, name):
        super().__init__(DataType.DT_COLOR, model, name, filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER)
