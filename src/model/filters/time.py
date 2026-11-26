"""Time-related filter subclasses.

Covers the time-input source, the event-counter sink, and the six switch-delay variants
(``on``/``off`` x ``8bit``/``16bit``/``float``). On- and off-delay filters with the same
data type share a subclass registered under both type codes.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT)
class TimeInput(StaticIOMixin, Filter):
    """Time source filter exposing a single float ``value`` output in milliseconds."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


@register_filter(FilterTypeEnumeration.FILTER_EVENT_COUNTER)
class EventCounter(StaticIOMixin, Filter):
    """Counts events and emits BPM / frequency estimates (16-bit)."""

    IN: ClassVar[dict[str, DataType]] = {"time": DataType.DT_DOUBLE}
    OUT: ClassVar[dict[str, DataType]] = {
        "bpm": DataType.DT_16_BIT,
        "freq": DataType.DT_16_BIT,
    }
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"event": "0:0"}


class _TimeDelayBase(StaticIOMixin, Filter):
    """Shared signature for the switch-delay filters.

    ``value_in`` and ``value`` share a data type (per the concrete subclass's ``_DT`` class
    attribute); ``time`` is always a float. The ``delay`` filter configuration defaults to
    ``"0.0"``. The user may edit it via the settings widget so
    :attr:`Filter.CONFIGURATION_SUPPORTED` stays at its ``True`` default.
    """

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"delay": "0.0"}

    def _rebuild_io(self) -> None:
        """Populate the per-instance I/O dicts from ``_DT`` and apply shared defaults."""
        dt = type(self)._DT
        self._in_data_types = {"value_in": dt, "time": DataType.DT_DOUBLE}
        self._out_data_types = {"value": dt}
        self._default_values = {}
        self._gui_update_keys = {}
        for key, value in self.DEFAULT_FILTER_CONFIGURATIONS.items():
            self._filter_configurations.setdefault(key, value)


@register_filter(FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_8BIT)
@register_filter(FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_8BIT)
class TimeDelay8Bit(_TimeDelayBase):
    """On- or off-delay for an 8-bit signal."""

    _DT: ClassVar[DataType] = DataType.DT_8_BIT


@register_filter(FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_16BIT)
@register_filter(FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_16BIT)
class TimeDelay16Bit(_TimeDelayBase):
    """On- or off-delay for a 16-bit signal."""

    _DT: ClassVar[DataType] = DataType.DT_16_BIT


@register_filter(FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_FLOAT)
@register_filter(FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_FLOAT)
class TimeDelayFloat(_TimeDelayBase):
    """On- or off-delay for a float signal."""

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
