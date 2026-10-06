"""Basic arithmetic filter nodes."""
from model import DataType
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.aggregating_filter_node import AggregatingFilterNode
from view.show_mode.editor.nodes.base.filternode import FilterNode


class ArithmeticMACNode(FilterNode):
    """Filter to calculate MAC value.

    value = (factor1 * factor2) + summand.

    """

    nodeName = "MAC filter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize MAC filter and add default values."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC, name=name)


class ArithmeticFloatTo16BitNode(FilterNode):
    """Filter to round a float/double value to a 16 bit value."""

    nodeName = "Float to 16 bit converter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_16BIT, name=name)


class ArithmeticFloatTo8BitNode(FilterNode):
    """Filter to round a float/double value to an 8 bit value."""

    nodeName = "Float to 8 bit converter"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT, name=name)


class ArithmeticRoundNode(FilterNode):
    """Filter to round a float/double value to a float/double value."""

    nodeName = "Round"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_ROUND, name=name)


class ArithmeticLogarithmNode(FilterNode):
    """Filter to calculate a logarithm value.

    value = ln(value_in).

    """

    nodeName = "log"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM, name=name)


class ArithmeticExponentialNode(FilterNode):
    """Filter to calculate an exponential value.

    value = exp(value_in)

    """

    nodeName = "exp"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL, name=name)


class ArithmeticMinimumNode(FilterNode):
    """Filter to calculate the minimum of two values.

    value = min(param1, param2)

    """

    nodeName = "min"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM, name=name)


class ArithmeticMaximumNode(FilterNode):
    """Filter to calculate the maximum of two values.

    value = max(param1, param2)

    """

    nodeName = "max"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM, name=name)


class Sum8BitNode(AggregatingFilterNode):
    """Filter node for sum filter.

    This filter accepts a configurable number of input channels and sums up all of their values.
    Datatype: 8bit.

    """

    nodeName = "8Bit Sum"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(DataType.DT_8_BIT, model, name, filter_type=FilterTypeEnumeration.FILTER_SUM_8BIT)


class Sum16BitNode(AggregatingFilterNode):
    """Filter node for sum filter.

    This filter accepts a configurable number of input channels and sums up all of their values.
    Datatype: 16bit.

    """

    nodeName = "16Bit Sum"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(DataType.DT_16_BIT, model, name, filter_type=FilterTypeEnumeration.FILTER_SUM_16BIT)


class SumFloatNode(AggregatingFilterNode):
    """Filter node for sum filter.

    This filter accepts a configurable number of input channels and sums up all of their values.
    Datatype: float.

    """

    nodeName = "Float Sum"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        """Initialize filter node."""
        super().__init__(DataType.DT_DOUBLE, model, name, filter_type=FilterTypeEnumeration.FILTER_SUM_FLOAT)
