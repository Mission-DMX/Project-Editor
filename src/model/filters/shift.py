"""Shift effect filter subclasses.

Each ``FILTER_EFFECT_SHIFT_*`` filter takes a typed ``input`` value together with ``time``
and ``switch_time`` (both ``float``) and distributes the input across a configurable number
of typed ``output_1`` ... ``output_N`` channels.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


class _ShiftBase(StaticIOMixin, Filter):
    """Shared logic for ``FILTER_EFFECT_SHIFT_*`` filters.

    Subclasses declare their forwarded data type via ``_DT``. The two time-related inputs are
    always floats (``time`` defaulting to ``"0"``, ``switch_time`` to ``"1000"`` ms). The
    number of output channels comes from ``filter_configurations["nr_outputs"]`` (default
    ``"0"``); each output is named ``output_{i+1}`` and typed as ``_DT``.
    """

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"nr_outputs": "0"}

    def _rebuild_io(self) -> None:
        """Apply defaults and derive the typed outputs from ``nr_outputs``."""
        super()._rebuild_io()
        dt = type(self)._DT
        self._in_data_types["input"] = dt
        self._in_data_types["switch_time"] = DataType.DT_DOUBLE
        self._in_data_types["time"] = DataType.DT_DOUBLE
        self._default_values["switch_time"] = "1000"
        self._default_values["time"] = "0"
        raw_count = self._filter_configurations.get("nr_outputs", "0")
        try:
            count = int(raw_count)
        except ValueError:
            count = 0
            self._filter_configurations["nr_outputs"] = "0"
        if count < 0:
            count = 0
        for i in range(count):
            self._out_data_types[f"output_{i + 1}"] = dt


@register_filter(FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT)
class Shift8Bit(_ShiftBase):
    """Shift effect over 8-bit input / outputs."""

    _DT: ClassVar[DataType] = DataType.DT_8_BIT


@register_filter(FilterTypeEnumeration.FILTER_EFFECT_SHIFT_16BIT)
class Shift16Bit(_ShiftBase):
    """Shift effect over 16-bit input / outputs."""

    _DT: ClassVar[DataType] = DataType.DT_16_BIT


@register_filter(FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT)
class ShiftFloat(_ShiftBase):
    """Shift effect over float input / outputs."""

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE


@register_filter(FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR)
class ShiftColor(_ShiftBase):
    """Shift effect over colour input / outputs."""

    _DT: ClassVar[DataType] = DataType.DT_COLOR
