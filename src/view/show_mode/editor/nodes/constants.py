# coding=utf-8
"""Constants filter nodes"""
from model import DataType

from . import FilterNode


class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = '8_bit_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=0, name=name, terminals={
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = '16_bit_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=1, name=name, terminals={
            'value': {'io': 'out'}
        })

        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0"
        self.filter.out_data_types["value"] = DataType.DT_16_BIT


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'Float_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=2, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0.0"
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'Color_filter'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=3, name=name, terminals={
            'value': {'io': 'out'}
        })
        try:
            self.filter.initial_parameters["value"] = model.initial_parameters["value"]
        except:
            self.filter.initial_parameters["value"] = "0,0,0"
        self.filter.out_data_types["value"] = DataType.DT_COLOR
