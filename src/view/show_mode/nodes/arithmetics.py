# coding=utf-8
"""Basic arithmetic filter nodes"""
from model import DataType
from . import FilterNode


class ArithmeticMACNode(FilterNode):
    """Filter to calculate MAC value.
    value = (factor1 * factor2) + summand
    """
    nodeName = 'MAC filter'

    def __init__(self, name):
        super().__init__(filter_type=10, name=name, terminals={
            'factor1': {'io': 'in'},
            'factor2': {'io': 'in'},
            'summand': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["factor1"] = DataType.DT_DOUBLE
        self._in_value_types["factor2"] = DataType.DT_DOUBLE
        self._in_value_types["summand"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArithmeticFloatTo16BitNode(FilterNode):
    """Filter to round a float/double value to a 16 bit value."""
    nodeName = 'Float to 16 bit converter'

    def __init__(self, name):
        super().__init__(filter_type=12, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_16_BIT


class ArithmeticFloatTo8BitNode(FilterNode):
    """Filter to round a float/double value to an 8 bit value."""
    nodeName = 'Float to 8 bit converter'

    def __init__(self, name):
        super().__init__(filter_type=13, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class ArithmeticRoundNode(FilterNode):
    """Filter to round a float/double value to a float/double value"""
    nodeName = 'Round'

    def __init__(self, name):
        super().__init__(filter_type=14, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArithmeticLogarithmNode(FilterNode):
    """Filter to calculate a logarithm value.
    value = ln(value_in)
    """
    nodeName = 'log'

    def __init__(self, name):
        super().__init__(filter_type=28, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArithmeticExponentialNode(FilterNode):
    """Filter to calculate an exponential value.
    value = exp(value_in)
    """
    nodeName = 'exp'

    def __init__(self, name):
        super().__init__(filter_type=29, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArithmeticMinimumNode(FilterNode):
    """Filter to calculate the minimum of two values.
    value = min(param1, param2)
    """
    nodeName = 'min'

    def __init__(self, name):
        super().__init__(filter_type=30, name=name, terminals={
            'param1': {'io': 'in'},
            'param2': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArithmeticMaximumNode(FilterNode):
    """Filter to calculate the maximum of two values.
    value = max(param1, param2)
    """
    nodeName = 'max'

    def __init__(self, name):
        super().__init__(filter_type=31, name=name, terminals={
            'param1': {'io': 'in'},
            'param2': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE
