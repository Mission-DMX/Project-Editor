"""Basic arithmetic filter nodes"""
from model import DataType
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.nodes.base.aggregating_filter_node import AggregatingFilterNode
from view.show_mode.editor.nodes.base.filternode import FilterNode


class ArithmeticMACNode(FilterNode):
    """Filter to calculate MAC value.
    value = (factor1 * factor2) + summand
    """
    nodeName = "MAC filter"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC, name=name, terminals={
            "factor1": {"io": "in"},
            "factor2": {"io": "in"},
            "summand": {"io": "in"},
            "value": {"io": "out"}
        })
        self.filter.in_data_types["factor1"] = DataType.DT_DOUBLE
        self.filter.in_data_types["factor2"] = DataType.DT_DOUBLE
        self.filter.in_data_types["summand"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.default_values["factor1"] = "1"
        self.filter.default_values["factor2"] = "1"
        self.filter.default_values["summand"] = "0"
        self.filter._configuration_supported = False


class ArithmeticFloatTo16BitNode(FilterNode):
    """Filter to round a float/double value to a 16 bit value."""
    nodeName = "Float to 16 bit converter"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_16BIT, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"}
                         })
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False


class ArithmeticFloatTo8BitNode(FilterNode):
    """Filter to round a float/double value to an 8 bit value."""
    nodeName = "Float to 8 bit converter"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"}
                         })
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_8_BIT
        self.filter._configuration_supported = False


class ArithmeticRoundNode(FilterNode):
    """Filter to round a float/double value to a float/double value"""
    nodeName = "Round"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_ROUND, name=name, terminals={
            "value_in": {"io": "in"},
            "value": {"io": "out"}
        })
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class ArithmeticLogarithmNode(FilterNode):
    """Filter to calculate a logarithm value.
    value = ln(value_in)
    """
    nodeName = "log"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"}
                         })
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.default_values["value_in"] = "1"
        self.filter._configuration_supported = False


class ArithmeticExponentialNode(FilterNode):
    """Filter to calculate an exponential value.
    value = exp(value_in)
    """
    nodeName = "exp"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL, name=name,
                         terminals={
                             "value_in": {"io": "in"},
                             "value": {"io": "out"}
                         })
        self.filter.in_data_types["value_in"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter._configuration_supported = False


class ArithmeticMinimumNode(FilterNode):
    """Filter to calculate the minimum of two values.
    value = min(param1, param2)
    """
    nodeName = "min"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM, name=name,
                         terminals={
                             "param1": {"io": "in"},
                             "param2": {"io": "in"},
                             "value": {"io": "out"}
                         })
        self.filter.in_data_types["param1"] = DataType.DT_DOUBLE
        self.filter.in_data_types["param2"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.default_values["param1"] = "1"
        self.filter.default_values["param2"] = "1"
        self.filter._configuration_supported = False


class ArithmeticMaximumNode(FilterNode):
    """Filter to calculate the maximum of two values.
    value = max(param1, param2)
    """
    nodeName = "max"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM, name=name,
                         terminals={
                             "param1": {"io": "in"},
                             "param2": {"io": "in"},
                             "value": {"io": "out"}
                         })
        self.filter.in_data_types["param1"] = DataType.DT_DOUBLE
        self.filter.in_data_types["param2"] = DataType.DT_DOUBLE
        self.filter.out_data_types["value"] = DataType.DT_DOUBLE
        self.filter.default_values["param1"] = "1"
        self.filter.default_values["param2"] = "1"
        self.filter._configuration_supported = False


class Sum8BitNode(AggregatingFilterNode):
    nodeName = "8Bit Sum"

    def __init__(self, model, name):
        super().__init__(DataType.DT_8_BIT, model, name, filter_type=FilterTypeEnumeration.FILTER_SUM_8BIT)


class Sum16BitNode(AggregatingFilterNode):
    nodeName = "16Bit Sum"

    def __init__(self, model, name):
        super().__init__(DataType.DT_16_BIT, model, name, filter_type=FilterTypeEnumeration.FILTER_SUM_16BIT)


class SumFloatNode(AggregatingFilterNode):
    nodeName = "Float Sum"

    def __init__(self, model, name):
        super().__init__(DataType.DT_DOUBLE, model, name, filter_type=FilterTypeEnumeration.FILTER_SUM_FLOAT)
