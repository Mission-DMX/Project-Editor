"""Trigonometric filter subclasses.

The six supported trig functions (``sin``, ``cos``, ``tan``, ``arcsin``, ``arccos``,
``arctan``) share the same five-input / one-output signature and the same default values
for ``factor_outer``/``factor_inner``/``phase``/``offset``. The arc variants add a non-zero
default for ``value_in`` so inverse functions do not fire on 0 at construction time.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


class _TrigBase(StaticIOMixin, Filter):
    """Common I/O signature for forward trig filters (sin/cos/tan)."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {
        "value_in": DataType.DT_DOUBLE,
        "factor_outer": DataType.DT_DOUBLE,
        "factor_inner": DataType.DT_DOUBLE,
        "phase": DataType.DT_DOUBLE,
        "offset": DataType.DT_DOUBLE,
    }
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {
        "factor_outer": "1",
        "factor_inner": "0.1",
        "phase": "0",
        "offset": "0",
    }


class _ArcTrigBase(_TrigBase):
    """Same signature as :class:`_TrigBase` plus a non-zero ``value_in`` default."""

    DEFAULT_VALUES: ClassVar[dict[str, str]] = {
        **_TrigBase.DEFAULT_VALUES,
        "value_in": "1",
    }


@register_filter(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN)
class TrigonometricSin(_TrigBase):
    """``value = factor_outer * sin((value_in + phase) * factor_inner) + offset``."""


@register_filter(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN)
class TrigonometricCos(_TrigBase):
    """``value = factor_outer * cos((value_in + phase) * factor_inner) + offset``."""


@register_filter(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_TANGENT)
class TrigonometricTangent(_TrigBase):
    """``value = factor_outer * tan((value_in + phase) * factor_inner) + offset``."""


@register_filter(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCSIN)
class TrigonometricArcSin(_ArcTrigBase):
    """``value = arcsin(value_in)`` (other inputs reserved for the forward form)."""


@register_filter(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCCOSIN)
class TrigonometricArcCos(_ArcTrigBase):
    """``value = arccos(value_in)``."""


@register_filter(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCTANGENT)
class TrigonometricArcTangent(_ArcTrigBase):
    """``value = arctan(value_in)``."""
