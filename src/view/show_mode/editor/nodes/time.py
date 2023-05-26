# coding=utf-8
"""Filter nodes related to time"""
from model import DataType

from . import FilterNode


class TimeNode(FilterNode):
    """Filter to represent time."""
    nodeName = 'Time'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=32, name=name, terminals={
            'value': {'io': 'out'}
        })
        self._out_value_types["value"] = DataType.DT_DOUBLE


class TimeSwitchOnDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time on-switch."""
    nodeName = 'Switch on delay - 8 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=33, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class TimeSwitchOnDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time on-switch."""
    nodeName = 'Switch on delay - 16 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=34, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class TimeSwitchOnDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time on-switch."""
    nodeName = 'Switch on delay - float'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=35, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class TimeSwitchOffDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time off-switch."""
    nodeName = 'Switch off delay - 8 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=36, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class TimeSwitchOffDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time off-switch."""
    nodeName = 'Switch off delay - 16 bit'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=37, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class TimeSwitchOffDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time off-switch."""
    nodeName = 'Switch off delay - float'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=38, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT
