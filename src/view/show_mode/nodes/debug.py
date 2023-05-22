# coding=utf-8
"""Debug filter nodes"""
from model import DataType
from . import FilterNode


class Debug8BitNode(FilterNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    nodeName = '8 Bit Filter (Debug)'

    def __init__(self, name):
        super().__init__(filter_type=4, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_8_BIT


class Debug16BitNode(FilterNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    nodeName = '16 Bit Filter (Debug)'

    def __init__(self, name):
        super().__init__(filter_type=5, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_16_BIT


class DebugFloatNode(FilterNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    nodeName = 'Float Filter (Debug)'

    def __init__(self, name):
        super().__init__(filter_type=6, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_DOUBLE


class DebugColorNode(FilterNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    nodeName = 'Color Filter (Debug)'

    def __init__(self, name):
        super().__init__(filter_type=7, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
