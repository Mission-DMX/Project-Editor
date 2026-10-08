"""Arithmetic filter subclasses.

Covers the static-I/O arithmetic filter types (MAC, round, log/exp, min/max, float-to-byte
converters). The aggregating ``FILTER_SUM_*`` variants have dynamic input counts and live
with the other aggregating filters, migrated in a later PR.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_MAC)
class ArithmeticMAC(StaticIOMixin, Filter):
    """``value = (factor1 * factor2) + summand`` over three float inputs."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {
        "factor1": DataType.DT_DOUBLE,
        "factor2": DataType.DT_DOUBLE,
        "summand": DataType.DT_DOUBLE,
    }
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {
        "factor1": "1.0",
        "factor2": "1.0",
        "summand": "0.0",
    }


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_16BIT)
class ArithmeticFloatTo16Bit(StaticIOMixin, Filter):
    """Rounds a float value to a 16-bit integer."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_DOUBLE}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT)
class ArithmeticFloatTo8Bit(StaticIOMixin, Filter):
    """Rounds a float value to an 8-bit integer."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_DOUBLE}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_8_BIT}


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_ROUND)
class ArithmeticRound(StaticIOMixin, Filter):
    """Rounds a float value to a float result."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_DOUBLE}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM)
class ArithmeticLogarithm(StaticIOMixin, Filter):
    """Natural logarithm: ``value = ln(value_in)``."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_DOUBLE}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {"value_in": "1"}


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL)
class ArithmeticExponential(StaticIOMixin, Filter):
    """Exponential: ``value = exp(value_in)``."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_DOUBLE}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


class _TwoParamArithmetic(StaticIOMixin, Filter):
    """Base signature for two-float-input / one-float-output arithmetic filters.

    Not registered on its own; shared by :class:`ArithmeticMinimum` and
    :class:`ArithmeticMaximum`.
    """

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {
        "param1": DataType.DT_DOUBLE,
        "param2": DataType.DT_DOUBLE,
    }
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {"param1": "1", "param2": "1"}


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM)
class ArithmeticMinimum(_TwoParamArithmetic):
    """``value = min(param1, param2)``."""


@register_filter(FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM)
class ArithmeticMaximum(_TwoParamArithmetic):
    """``value = max(param1, param2)``."""
