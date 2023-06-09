# coding=utf-8
"""Adapters and converters filter nodes"""
from model import DataType

from . import FilterNode


class Adapter16BitTo8BitNode(FilterNode):
    """Filter to convert a 16 bit value to two 8 bit values."""
    nodeName = '16 bit to 8 bit converter'

    def __init__(self, name):
        super().__init__(filter_type=8, name=name, terminals={
            'value': {'io': 'in'},
            'value_lower': {'io': 'out'},
            'value_upper': {'io': 'out'},
        })
        self._in_value_types["value"] = DataType.DT_16_BIT
        self._out_value_types["value_lower"] = DataType.DT_8_BIT
        self._out_value_types["value_upper"] = DataType.DT_8_BIT


class Adapter16BitToBoolNode(FilterNode):
    """Filter to convert a 16 bit value to a boolean.
    If input is 0, output is 0, else 1.
    """
    nodeName = '16 bit to bool converter'

    def __init__(self, name):
        super().__init__(filter_type=9, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_16_BIT
        self._out_value_types["value"] = DataType.DT_BOOL


class AdapterColorToRGBNode(FilterNode):
    """Filter to convert a color value to a rgb value."""
    nodeName = 'Color to rgb converter'

    def __init__(self, name):
        super().__init__(filter_type=15, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
        self._out_value_types["r"] = DataType.DT_8_BIT
        self._out_value_types["g"] = DataType.DT_8_BIT
        self._out_value_types["b"] = DataType.DT_8_BIT


class AdapterColorToRGBWNode(FilterNode):
    """Filter to convert a color value to a rgbw value."""
    nodeName = 'Color to rgb-w converter'

    def __init__(self, name):
        super().__init__(filter_type=16, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
        self._out_value_types["r"] = DataType.DT_8_BIT
        self._out_value_types["g"] = DataType.DT_8_BIT
        self._out_value_types["b"] = DataType.DT_8_BIT
        self._out_value_types["w"] = DataType.DT_8_BIT


class AdapterColorToRGBWANode(FilterNode):
    """Filter to convert a color value to a RGBWA value."""
    nodeName = 'Color to rgb-wa converter'

    def __init__(self, name):
        super().__init__(filter_type=17, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'},
            'a': {'io': 'out'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
        self._out_value_types["r"] = DataType.DT_8_BIT
        self._out_value_types["g"] = DataType.DT_8_BIT
        self._out_value_types["b"] = DataType.DT_8_BIT
        self._out_value_types["w"] = DataType.DT_8_BIT
        self._out_value_types["a"] = DataType.DT_8_BIT


class AdapterFloatToColorNode(FilterNode):
    """Filter to convert a float/double value to a color value."""
    nodeName = 'Float to color converter'

    def __init__(self, name):
        super().__init__(filter_type=18, name=name, terminals={
            'h': {'io': 'in'},
            's': {'io': 'in'},
            'i': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["h"] = DataType.DT_DOUBLE
        self._in_value_types["s"] = DataType.DT_DOUBLE
        self._in_value_types["i"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_COLOR
