# coding=utf-8
"""Filter nodes related to time"""
from model import DataType
from model.filter import FilterTypeEnumeration

from view.show_mode.editor.nodes.base.filternode import FilterNode


class TimeNode(FilterNode):
    """Filter to represent time."""
    nodeName = 'Time'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT, name=name, terminals={
            'value': {'io': 'out'}
        })
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE


class TimeSwitchOnDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time on-switch."""
    nodeName = 'Switch on delay - 8 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=33, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["delay"] = model.filter_configurations["delay"]
        except:
            self.filter.filter_configurations["delay"] = "0.0"

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class TimeSwitchOnDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time on-switch."""
    nodeName = 'Switch on delay - 16 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=34, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["delay"] = model.filter_configurations["delay"]
        except:
            self.filter.filter_configurations["delay"] = "0.0"

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class TimeSwitchOnDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time on-switch."""
    nodeName = 'Switch on delay - float'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=35, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["delay"] = model.filter_configurations["delay"]
        except:
            self.filter.filter_configurations["delay"] = "0.0"

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class TimeSwitchOffDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time off-switch."""
    nodeName = 'Switch off delay - 8 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=36, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })

        try:
            self.filter.filter_configurations["delay"] = model.filter_configurations["delay"]
        except:
            self.filter.filter_configurations["delay"] = "0.0"

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class TimeSwitchOffDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time off-switch."""
    nodeName = 'Switch off delay - 16 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=37, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })

        try:
            self.filter.filter_configurations["delay"] = model.filter_configurations["delay"]
        except:
            self.filter.filter_configurations["delay"] = "0.0"

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT


class TimeSwitchOffDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time off-switch."""
    nodeName = 'Switch off delay - float'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=38, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["delay"] = model.filter_configurations["delay"]
        except:
            self.filter.filter_configurations["delay"] = "0.0"

        self.filter.in_data_types["value_in"] = DataType.DT_8_BIT
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT
