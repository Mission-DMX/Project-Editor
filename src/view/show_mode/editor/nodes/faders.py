# coding=utf-8
"""Column fader filter nodes"""
from model import DataType

from . import FilterNode


class FaderRawNode(FilterNode):
    """Filter to represent any filter fader"""
    nodeName = "Raw"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=39, name=name, terminals={
            'fader': {'io': 'out'},
            'encoder': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["fader"] = DataType.DT_16_BIT
        self._out_value_types["encoder"] = DataType.DT_16_BIT


class FaderHSINode(FilterNode):
    """Filter to represent a hsi filter fader"""
    nodeName = "HSI"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=40, name=name, terminals={
            'color': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR


class FaderHSIANode(FilterNode):
    """Filter to represent a hsia filter fader"""
    nodeName = "HSI-A"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=41, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR
        self._out_value_types["amber"] = DataType.DT_8_BIT


class FaderHSIUNode(FilterNode):
    """Filter to represent a hsiu filter fader"""
    nodeName = "HSI_U"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=42, name=name, terminals={
            'color': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR
        self._out_value_types["uv"] = DataType.DT_8_BIT


class FaderHSIAUNode(FilterNode):
    """Filter to represent a hasiau filter fader"""
    nodeName = "HSI-AU"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=43, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR
        self._out_value_types["amber"] = DataType.DT_8_BIT
        self._out_value_types["uv"] = DataType.DT_8_BIT
