"""Wave-generator filter subclasses.

Triangle and sawtooth share the trigonometric base signature exactly; square adds a
``length`` input (duty-cycle length in degrees) with a default of ``180``.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, FilterTypeEnumeration

from .factory import register_filter
from .trigonometrics import _TrigBase


@register_filter(FilterTypeEnumeration.FILTER_WAVES_TRIANGLE)
class WaveTriangle(_TrigBase):
    """Triangle wave generator sharing the trig filter's input signature."""


@register_filter(FilterTypeEnumeration.FILTER_WAVES_SAWTOOTH)
class WaveSawtooth(_TrigBase):
    """Sawtooth wave generator sharing the trig filter's input signature."""


@register_filter(FilterTypeEnumeration.FILTER_WAVES_SQUARE)
class WaveSquare(_TrigBase):
    """Square wave generator; extends the trig signature with a ``length`` input (degrees)."""

    IN: ClassVar[dict[str, DataType]] = {**_TrigBase.IN, "length": DataType.DT_DOUBLE}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {**_TrigBase.DEFAULT_VALUES, "length": "180"}
