"""Series strobe generator filter subclasses.

Three variants (``8bit``/``16bit``/``float``) share the signature: a brightness input
whose data type matches the variant, two 8-bit control inputs (``frequency`` and
``duty_cycle``), and one output (``value``) that mirrors the brightness data type.
The ``slowest_period_ms`` configuration selects the full-cycle period picked when
``frequency == 1``; higher input values interpolate linearly up to 20 Hz.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


class _StrobeGeneratorBase(StaticIOMixin, Filter):
    """Shared signature for the ``filter_series_strobe_generator_*`` family."""

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"slowest_period_ms": "500.0"}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {
        "brightness": "0",
        "frequency": "0",
        "duty_cycle": "128",
    }

    def _rebuild_io(self) -> None:
        """Populate the per-instance I/O dicts from ``_DT`` and apply shared defaults."""
        dt = type(self)._DT
        self._in_data_types = {
            "brightness": dt,
            "frequency": DataType.DT_8_BIT,
            "duty_cycle": DataType.DT_8_BIT,
        }
        self._out_data_types = {"value": dt}
        self._default_values = dict(self.DEFAULT_VALUES)
        self._gui_update_keys = {}
        for key, value in self.DEFAULT_FILTER_CONFIGURATIONS.items():
            self._filter_configurations.setdefault(key, value)


@register_filter(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_8BIT)
class StrobeGenerator8Bit(_StrobeGeneratorBase):
    """8-bit series strobe generator."""

    _DT: ClassVar[DataType] = DataType.DT_8_BIT


@register_filter(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_16BIT)
class StrobeGenerator16Bit(_StrobeGeneratorBase):
    """16-bit series strobe generator."""

    _DT: ClassVar[DataType] = DataType.DT_16_BIT


@register_filter(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
class StrobeGeneratorFloat(_StrobeGeneratorBase):
    """Float series strobe generator."""

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
