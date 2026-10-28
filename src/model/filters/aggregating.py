"""Aggregating filter subclasses (sum variants and native colour mixers).

These filters have a configurable number of same-typed inputs (named ``"0"``, ``"1"``, ...)
that fold into a single typed output ``"value"``. The input count comes from
``filter_configurations["input_count"]``.

The virtual-filter colour mixer (``VFILTER_COLOR_MIXER``) is not migrated here; it continues
to use the view-side :class:`view.show_mode.editor.nodes.base.aggregating_filter_node.AggregatingFilterNode`
until the virtual-filter pass.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter

_DEFAULT_FOR_DT: dict[DataType, str] = {
    DataType.DT_8_BIT: "0",
    DataType.DT_16_BIT: "0",
    DataType.DT_DOUBLE: "0.0",
    DataType.DT_COLOR: "0,0,0",
    DataType.DT_BOOL: "0",
}


class _AggregatingFilterBase(StaticIOMixin, Filter):
    """Shared logic for N-typed-inputs / one-typed-output aggregator filters.

    Subclasses declare their aggregated data type on the ``_DT`` class attribute. The input
    count is read from the ``input_count`` configuration (default ``"2"``); each input is
    named by its index as a string and uses the data-type-specific default value.
    """

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"input_count": "2"}

    def _rebuild_io(self) -> None:
        """Apply defaults and derive ``in_data_types`` / ``out_data_types`` from ``input_count``."""
        super()._rebuild_io()
        dt = type(self)._DT
        self._out_data_types["value"] = dt
        raw_count = self._filter_configurations.get("input_count", "2")
        try:
            count = int(raw_count)
        except ValueError:
            count = 0
            self._filter_configurations["input_count"] = "0"
        if count < 0:
            count = 0
        default = _DEFAULT_FOR_DT.get(dt, "0")
        for i in range(count):
            name = str(i)
            self._in_data_types[name] = dt
            self._default_values[name] = default


@register_filter(FilterTypeEnumeration.FILTER_SUM_8BIT)
class Sum8Bit(_AggregatingFilterBase):
    """8-bit sum of a configurable number of inputs."""

    _DT: ClassVar[DataType] = DataType.DT_8_BIT


@register_filter(FilterTypeEnumeration.FILTER_SUM_16BIT)
class Sum16Bit(_AggregatingFilterBase):
    """16-bit sum of a configurable number of inputs."""

    _DT: ClassVar[DataType] = DataType.DT_16_BIT


@register_filter(FilterTypeEnumeration.FILTER_SUM_FLOAT)
class SumFloat(_AggregatingFilterBase):
    """Float sum of a configurable number of inputs."""

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE


@register_filter(FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV)
class ColorMixerHSV(_AggregatingFilterBase):
    """Colour mixer using the HSV algorithm."""

    _DT: ClassVar[DataType] = DataType.DT_COLOR


@register_filter(FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB)
class ColorMixerAdditiveRGB(_AggregatingFilterBase):
    """Colour mixer using additive RGB combination."""

    _DT: ClassVar[DataType] = DataType.DT_COLOR


@register_filter(FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATIVE_RGB)
class ColorMixerNormativeRGB(_AggregatingFilterBase):
    """Colour mixer using normative RGB combination."""

    _DT: ClassVar[DataType] = DataType.DT_COLOR
