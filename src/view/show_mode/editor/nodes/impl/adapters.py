# coding=utf-8
"""Adapters and converters filter nodes"""
from model import DataType, Scene
from model.filter import FilterTypeEnumeration, Filter

from view.show_mode.editor.nodes.base.filternode import FilterNode


class Adapter16BitTo8BitNode(FilterNode):
    """Filter to convert a 16 bit value to two 8 bit values."""
    nodeName = '16 bit to 8 bit converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=int(FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT), name=name, terminals={
            'value': {'io': 'in'},
            'value_lower': {'io': 'out'},
            'value_upper': {'io': 'out'},
        })
        self.filter.in_data_types["value"] = DataType.DT_16_BIT
        self.filter.out_data_types["value_lower"] = DataType.DT_8_BIT
        self.filter.out_data_types["value_upper"] = DataType.DT_8_BIT


class Adapter16BitToBoolNode(FilterNode):
    """Filter to convert a 16 bit value to a boolean.
    If input is 0, output is 0, else 1.
    """
    nodeName = '16 bit to bool converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.in_data_types["value_in"] = DataType.DT_16_BIT
        self.filter.out_data_types["value"] = DataType.DT_BOOL


class Adapter16bitToFloat(FilterNode):
    nodeName = "16bit to Float converter"

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })

        self.filter.in_data_types["value_in"] = DataType.DT_16_BIT
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class Adapter8bitToFloat(FilterNode):
    nodeName = "8bit to Float converter"

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class AdapterColorToRGBNode(FilterNode):
    """Filter to convert a color value to a rgb value."""
    nodeName = 'Color to rgb converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter.out_data_types["r"] = DataType.DT_8_BIT
        self.filter.out_data_types["g"] = DataType.DT_8_BIT
        self.filter.out_data_types["b"] = DataType.DT_8_BIT


class AdapterColorToRGBWNode(FilterNode):
    """Filter to convert a color value to a rgbw value."""
    nodeName = 'Color to rgb-w converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'}
        })
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter.out_data_types["r"] = DataType.DT_8_BIT
        self.filter.out_data_types["g"] = DataType.DT_8_BIT
        self.filter.out_data_types["b"] = DataType.DT_8_BIT
        self.filter.out_data_types["w"] = DataType.DT_8_BIT


class AdapterColorToRGBWANode(FilterNode):
    """Filter to convert a color value to a RGBWA value."""
    nodeName = 'Color to rgb-wa converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBWA, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'},
            'a': {'io': 'out'}
        })
        self.filter.in_data_types["value"] = DataType.DT_COLOR
        self.filter.out_data_types["r"] = DataType.DT_8_BIT
        self.filter.out_data_types["g"] = DataType.DT_8_BIT
        self.filter.out_data_types["b"] = DataType.DT_8_BIT
        self.filter.out_data_types["w"] = DataType.DT_8_BIT
        self.filter.out_data_types["a"] = DataType.DT_8_BIT


class AdapterFloatToColorNode(FilterNode):
    """Filter to convert a float/double value to a color value."""
    nodeName = 'Float to color converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR, name=name, terminals={
            'h': {'io': 'in'},
            's': {'io': 'in'},
            'i': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.in_data_types["h"] = DataType.DT_DOUBLE
        self.filter.in_data_types["s"] = DataType.DT_DOUBLE
        self.filter.in_data_types["i"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_COLOR


class AdapterColorToFloatsNode(FilterNode):
    """Filter that splits the HSI values into three individual float channels."""
    nodeName = 'Color to Float converter'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT, name=name, terminals={
            'input': {'io': 'in'},
            'h': {'io': 'out'},
            's': {'io': 'out'},
            'i': {'io': 'out'},
        })
        self.filter.in_data_types["input"] = DataType.DT_COLOR
        self.filter.out_data_types["h"] = DataType.DT_DOUBLE
        self.filter.out_data_types["s"] = DataType.DT_DOUBLE
        self.filter.out_data_types["i"] = DataType.DT_DOUBLE

class AdapterFloatToRange(FilterNode):
    """Filter maps a range of float to another range of specific type (template)"""

    def __init__(self, model: Filter | Scene, name: str, filter_type: FilterTypeEnumeration):
        super().__init__(model, int(filter_type), name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["lower_bound_in"] = model.initial_parameters["lower_bound_in"]
            self.filter.initial_parameters["upper_bound_in"] = model.initial_parameters["upper_bound_in"]
            self.filter.initial_parameters["lower_bound_out"] = model.initial_parameters["lower_bound_out"]
            self.filter.initial_parameters["limit_range"] = model.initial_parameters["limit_range"]
        except:
            self.filter.initial_parameters["lower_bound_in"] = "0"
            self.filter.initial_parameters["upper_bound_in"] = "1"
            self.filter.initial_parameters["lower_bound_out"] = "0"
            self.filter.initial_parameters["limit_range"] = "0"
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["lower_bound_in"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["upper_bound_in"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["lower_bound_out"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["upper_bound_out"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["limit_range"] = DataType.DT_BOOL

class AdapterFloatTo8BitRange(AdapterFloatToRange):
    """Filter maps a range of float to a range of 8bit"""
    nodeName = 'Float range to 8bit'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE, name=name)
        try:
            self.filter.initial_parameters["upper_bound_out"] = model.initial_parameters["upper_bound_out"]
        except:
            self.filter.initial_parameters["upper_bound_out"] = "255"
        self.filter.out_data_types["value"] = DataType.DT_8_BIT

class AdapterFloatTo16BitRange(AdapterFloatToRange):
    """Filter maps a range of float to a range of 16bit"""
    nodeName = 'Float range to 16bit'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE, name=name)
        try:
            self.filter.initial_parameters["upper_bound_out"] = model.initial_parameters["upper_bound_out"]
        except:
            self.filter.initial_parameters["upper_bound_out"] = "65535"
        self.filter.out_data_types["value"] = DataType.DT_16_BIT

class AdapterFloatToFloatRange(AdapterFloatToRange):
    """Filter maps a range of float to a range of float"""
    nodeName = 'Float range to float range'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE, name=name)
        try:
            self.filter.initial_parameters["upper_bound_out"] = model.initial_parameters["upper_bound_out"]
        except:
            self.filter.initial_parameters["upper_bound_out"] = "1"
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE

class CombineTwo8BitToSingle16Bit(FilterNode):
    """Filter that combines two 8bit values to a 16bit one."""
    nodeName = 'Dual 8bit to single 16bit'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT, name=name, terminals={
            'lower': {'io': 'in'},
            'upper': {'io': 'in'},
            'value': {'io': 'out'},
        })
        self.filter.in_data_types["lower"] = DataType.DT_8_BIT
        self.filter.in_data_types["upper"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_16_BIT

class Map8BitTo16Bit(FilterNode):
    """Filter that maps an 8bit value to a 16bit one."""
    nodeName = 'Map 8bit to 16bit'

    def __init__(self, model: Filter | Scene, name: str):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'},
        })
        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
