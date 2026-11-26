"""Adapter / converter filter subclasses.

One subclass per native-filter :class:`~model.filter.FilterTypeEnumeration` value handled by
:mod:`view.show_mode.editor.nodes.impl.adapters`. These subclasses own the I/O signature and
any default initial parameters so a constructed filter is fully usable without the
corresponding node ever being instantiated.

Virtual-filter wrapper node classes in ``impl/adapters.py`` (e.g. the dimmer brightness
mixin, color-to-colorwheel) continue to drive their underlying v-filter instances until
their respective virtual filters are migrated in a later PR.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT)
class Adapter16BitToDual8Bit(StaticIOMixin, Filter):
    """Splits a 16-bit value into its high and low 8-bit halves."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}
    OUT: ClassVar[dict[str, DataType]] = {
        "value_lower": DataType.DT_8_BIT,
        "value_upper": DataType.DT_8_BIT,
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL)
class Adapter16BitToBool(StaticIOMixin, Filter):
    """Converts a 16-bit value to a boolean (0 -> 0, non-zero -> 1)."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_16_BIT}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_BOOL}


@register_filter(FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT)
class Adapter16BitToFloat(StaticIOMixin, Filter):
    """Normalises a 16-bit value to a float in ``[0, 1]``."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_16_BIT}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


@register_filter(FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT)
class Adapter8BitToFloat(StaticIOMixin, Filter):
    """Normalises an 8-bit value to a float in ``[0, 1]``."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_8_BIT}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB)
class AdapterColorToRGB(StaticIOMixin, Filter):
    """Splits a colour value into its 8-bit R, G, B channels."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_COLOR}
    OUT: ClassVar[dict[str, DataType]] = {
        "r": DataType.DT_8_BIT,
        "g": DataType.DT_8_BIT,
        "b": DataType.DT_8_BIT,
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW)
class AdapterColorToRGBW(StaticIOMixin, Filter):
    """Splits a colour value into its 8-bit R, G, B, W channels."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_COLOR}
    OUT: ClassVar[dict[str, DataType]] = {
        "r": DataType.DT_8_BIT,
        "g": DataType.DT_8_BIT,
        "b": DataType.DT_8_BIT,
        "w": DataType.DT_8_BIT,
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBWA)
class AdapterColorToRGBWA(StaticIOMixin, Filter):
    """Splits a colour value into its 8-bit R, G, B, W, A channels."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_COLOR}
    OUT: ClassVar[dict[str, DataType]] = {
        "r": DataType.DT_8_BIT,
        "g": DataType.DT_8_BIT,
        "b": DataType.DT_8_BIT,
        "w": DataType.DT_8_BIT,
        "a": DataType.DT_8_BIT,
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR)
class AdapterFloatToColor(StaticIOMixin, Filter):
    """Builds a colour value from three HSI float channels, defaulting ``i`` to 1."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {
        "h": DataType.DT_DOUBLE,
        "s": DataType.DT_DOUBLE,
        "i": DataType.DT_DOUBLE,
    }
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_COLOR}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {"i": "1"}


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT)
class AdapterColorToFloat(StaticIOMixin, Filter):
    """Splits a colour value into three HSI float channels."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"input": DataType.DT_COLOR}
    OUT: ClassVar[dict[str, DataType]] = {
        "h": DataType.DT_DOUBLE,
        "s": DataType.DT_DOUBLE,
        "i": DataType.DT_DOUBLE,
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT)
class AdapterDualByteTo16Bit(StaticIOMixin, Filter):
    """Combines two 8-bit inputs (``lower``, ``upper``) into a single 16-bit value."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {
        "lower": DataType.DT_8_BIT,
        "upper": DataType.DT_8_BIT,
    }
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT)
class Adapter8BitTo16Bit(StaticIOMixin, Filter):
    """Maps an 8-bit value to its 16-bit equivalent."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_8_BIT}
    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}


class _FloatToRangeBase(StaticIOMixin, Filter):
    """Common I/O signature and defaults for the ``FLOAT_TO_*_RANGE`` native adapters.

    Shared by the three concrete subclasses below. Not registered itself; each registered
    subclass overrides ``OUT`` with its output data type and extends
    ``DEFAULT_INITIAL_PARAMETERS`` with the appropriate ``upper_bound_out`` value.
    """

    IN: ClassVar[dict[str, DataType]] = {"value_in": DataType.DT_DOUBLE}
    GUI_UPDATE_KEYS: ClassVar[dict[str, DataType | list[str]]] = {
        "lower_bound_in": DataType.DT_DOUBLE,
        "upper_bound_in": DataType.DT_DOUBLE,
        "lower_bound_out": DataType.DT_DOUBLE,
        "upper_bound_out": DataType.DT_DOUBLE,
        "limit_range": DataType.DT_BOOL,
    }
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {
        "lower_bound_in": "0",
        "upper_bound_in": "1",
        "lower_bound_out": "0",
        "upper_bound_out": "1",
        "limit_range": "0",
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE)
class AdapterFloatToFloatRange(_FloatToRangeBase):
    """Maps a float range to another float range."""

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE)
class AdapterFloatTo8BitRange(_FloatToRangeBase):
    """Maps a float range to an 8-bit range; defaults ``upper_bound_out`` to 255."""

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_8_BIT}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {
        **_FloatToRangeBase.DEFAULT_INITIAL_PARAMETERS,
        "upper_bound_out": "255",
    }


@register_filter(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE)
class AdapterFloatTo16BitRange(_FloatToRangeBase):
    """Maps a float range to a 16-bit range; defaults ``upper_bound_out`` to 65535."""

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {
        **_FloatToRangeBase.DEFAULT_INITIAL_PARAMETERS,
        "upper_bound_out": "65535",
    }
