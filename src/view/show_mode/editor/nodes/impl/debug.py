# coding=utf-8
"""Debug filter nodes"""
from model import DataType

from view.show_mode.editor.nodes.base.filternode import FilterNode


class DebugNode(FilterNode):
    """Basic debug node"""
    def __init__(self, model, name, filter_type):
        super().__init__(model, filter_type, name, terminals={
            'value': {'io': 'in'}
        })


class Debug8BitNode(DebugNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    nodeName = '8 Bit Filter (Debug)'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=4, name=name)
        self.filter.in_data_types["value"] = DataType.DT_8_BIT


class Debug16BitNode(DebugNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    nodeName = '16 Bit Filter (Debug)'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=5, name=name)
        self.filter.in_data_types["value"] = DataType.DT_16_BIT


class DebugFloatNode(DebugNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    nodeName = 'Float Filter (Debug)'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=6, name=name)
        self.filter.in_data_types["value"] = DataType.DT_DOUBLE


class DebugColorNode(DebugNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    nodeName = 'Color Filter (Debug)'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=7, name=name)
        self.filter.in_data_types["value"] = DataType.DT_COLOR
