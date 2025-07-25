"""Adapters and converters filter nodes"""
from model import DataType, Scene
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class Adapter16BitTo8BitNode(FilterNode):
    """Filter to convert a 16 bit value to two 8 bit values."""
    nodeName = "16 bit to 8 bit converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=int(FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT),
                         name=name, terminals={
                "value": {"io": "in"},
                "value_lower": {"io": "out"},
                "value_upper": {"io": "out"},
            })
        self.filter.in_data_types["value"] = DataType.DT_16_BIT
        self.filter.out_data_types["value_lower"] = DataType.DT_8_BIT
        self.filter.out_data_types["value_upper"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class Adapter16BitToBoolNode(FilterNode):
    """Filter to convert a 16 bit value to a boolean.
    If input is 0, output is 0, else 1.
    """
    nodeName = "16 bit to bool converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"},
                         })
        self.filter.in_data_types["value_in"] = DataType.DT_16_BIT
        self.filter.out_data_types["value"] = DataType.DT_BOOL
        self.filter._configuration_supported = False


class Adapter16bitToFloat(FilterNode):
    nodeName = "16bit to Float converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"},
                         })

        self.filter.in_data_types["value_in"] = DataType.DT_16_BIT
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class Adapter8bitToFloat(FilterNode):
    nodeName = "8bit to Float converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"},
                         })

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class AdapterColorToRGBNode(FilterNode):
    """Filter to convert a color value to a rgb value."""
    nodeName = "Color to rgb converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB, name=name,
                         terminals={
                             "value": {"io": "in"},
                             "r": {"io": "out"},
                             "g": {"io": "out"},
                             "b": {"io": "out"},
                         })
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter.out_data_types["r"] = DataType.DT_8_BIT
        self.filter.out_data_types["g"] = DataType.DT_8_BIT
        self.filter.out_data_types["b"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class AdapterColorToRGBWNode(FilterNode):
    """Filter to convert a color value to a rgbw value."""
    nodeName = "Color to rgb-w converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW, name=name,
                         terminals={
                             "value": {"io": "in"},
                             "r": {"io": "out"},
                             "g": {"io": "out"},
                             "b": {"io": "out"},
                             "w": {"io": "out"},
                         })
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter.out_data_types["r"] = DataType.DT_8_BIT
        self.filter.out_data_types["g"] = DataType.DT_8_BIT
        self.filter.out_data_types["b"] = DataType.DT_8_BIT
        self.filter.out_data_types["w"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class AdapterColorToRGBWANode(FilterNode):
    """Filter to convert a color value to a RGBWA value."""
    nodeName = "Color to rgb-wa converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBWA, name=name,
                         terminals={
                             "value": {"io": "in"},
                             "r": {"io": "out"},
                             "g": {"io": "out"},
                             "b": {"io": "out"},
                             "w": {"io": "out"},
                             "a": {"io": "out"},
                         })
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter.out_data_types["r"] = DataType.DT_8_BIT
        self.filter.out_data_types["g"] = DataType.DT_8_BIT
        self.filter.out_data_types["b"] = DataType.DT_8_BIT
        self.filter.out_data_types["w"] = DataType.DT_8_BIT
        self.filter.out_data_types["a"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class AdapterFloatToColorNode(FilterNode):
    """Filter to convert a float/double value to a color value."""
    nodeName = "Float to color converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR, name=name,
                         terminals={
                             "h": {"io": "in"},
                             "s": {"io": "in"},
                             "i": {"io": "in"},
                             "value": {"io": "out"},
                         })
        self.filter.in_data_types["h"] = DataType.DT_DOUBLE
        self.filter.in_data_types["s"] = DataType.DT_DOUBLE
        self.filter.in_data_types["i"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_COLOR
        self.filter.default_values["i"] = "1"
        self.filter._configuration_supported = False


class AdapterColorToFloatsNode(FilterNode):
    """Filter that splits the HSI values into three individual float channels."""
    nodeName = "Color to Float converter"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT, name=name,
                         terminals={
                             "input": {"io": "in"},
                             "h": {"io": "out"},
                             "s": {"io": "out"},
                             "i": {"io": "out"},
                         })
        self.filter.in_data_types["input"] = DataType.DT_COLOR
        self.filter.out_data_types["h"] = DataType.DT_DOUBLE
        self.filter.out_data_types["s"] = DataType.DT_DOUBLE
        self.filter.out_data_types["i"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class AdapterFloatToRange(FilterNode):
    """Filter maps a range of floats to another range of specific type (template)"""

    nodeName = "float range to float range"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str,
                 filter_type: FilterTypeEnumeration =
                 FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE) -> None:
        super().__init__(model, int(filter_type), name, terminals={
            "value_in": {"io": "in"},
            "value": {"io": "out"},
        })

        try:
            self.filter.initial_parameters["lower_bound_in"] = model.initial_parameters["lower_bound_in"]
        except:
            self.filter.initial_parameters["lower_bound_in"] = "0"
        try:
            self.filter.initial_parameters["upper_bound_in"] = model.initial_parameters["upper_bound_in"]
        except:
            self.filter.initial_parameters["upper_bound_in"] = "1"
        try:
            self.filter.initial_parameters["lower_bound_out"] = model.initial_parameters["lower_bound_out"]
        except:
            self.filter.initial_parameters["lower_bound_out"] = "0"
        try:
            self.filter.initial_parameters["upper_bound_out"] = model.initial_parameters["upper_bound_out"]
        except:
            self.filter.initial_parameters["upper_bound_out"] = "1"
        try:
            self.filter.initial_parameters["limit_range"] = model.initial_parameters["limit_range"]
        except:
            self.filter.initial_parameters["limit_range"] = "0"
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["lower_bound_in"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["upper_bound_in"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["lower_bound_out"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["upper_bound_out"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["limit_range"] = DataType.DT_BOOL


class AdapterFloatTo8BitRange(AdapterFloatToRange):
    """Filter maps a range of float to a range of 8bit"""
    nodeName = "Float range to 8bit"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE, name=name)
        try:
            self.filter.initial_parameters["upper_bound_out"] = model.initial_parameters["upper_bound_out"]
        except:
            self.filter.initial_parameters["upper_bound_out"] = "255"
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class AdapterFloatTo16BitRange(AdapterFloatToRange):
    """Filter maps a range of float to a range of 16bit"""
    nodeName = "Float range to 16bit"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE, name=name)
        try:
            self.filter.initial_parameters["upper_bound_out"] = model.initial_parameters["upper_bound_out"]
        except:
            self.filter.initial_parameters["upper_bound_out"] = "65535"
        self.filter.out_data_types["value"] = DataType.DT_16_BIT


class Adapter16BitToRangeFloat(AdapterFloatToRange):
    """Filter maps a range of 16bit to a range of float"""
    nodeName = "16bit range to Float"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE,
                         name=name)
        try:
            self.filter.initial_parameters["upper_bound_in"] = model.initial_parameters["upper_bound_in"]
        except:
            self.filter.initial_parameters["upper_bound_in"] = "65535"
        self.filter.in_data_types["value_in"] = DataType.DT_16_BIT
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class Adapter8BitToRangeFloat(AdapterFloatToRange):
    """Filter maps a range of 8bit to a range of floats"""
    nodeName = "8bit range to Float"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE,
                         name=name)
        try:
            self.filter.initial_parameters["upper_bound_in"] = model.initial_parameters["upper_bound_in"]
        except:
            self.filter.initial_parameters["upper_bound_in"] = "255"
        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class CombineTwo8BitToSingle16Bit(FilterNode):
    """Filter that combines two 8bit values to a 16bit one."""
    nodeName = "Dual 8bit to single 16bit"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT, name=name,
                         terminals={
                             "lower": {"io": "in"},
                             "upper": {"io": "in"},
                             "value": {"io": "out"},
                         })
        self.filter.in_data_types["lower"] = DataType.DT_8_BIT
        self.filter.in_data_types["upper"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False


class Map8BitTo16Bit(FilterNode):
    """Filter that maps an 8-Bit value to a 16-Bit one."""
    nodeName = "Map 8bit to 16bit"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"},
                         })
        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False


class ColorBrightnessMixinNode(FilterNode):
    nodeName = "Color Brightness Mixin"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN,
                         name=name, terminals={
                "out": {"io": "out"},
                "color_in": {"io": "in"},
                "brightness": {"io": "in"},
            },
                         )
        self.filter.out_data_types["out"] = DataType.DT_COLOR
        self.filter.in_data_types["color_in"] = DataType.DT_COLOR
        self.filter.in_data_types["brightness"] = DataType.DT_8_BIT
        self.channel_hints["brightness"] = "[0-255, optional]"
        self.filter._configuration_supported = False
