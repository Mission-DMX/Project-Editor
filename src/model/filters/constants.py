"""Constant filter subclasses.

One subclass per native-filter ``FILTER_CONSTANT_*`` and ``FILTER_RESPONDING_CONSTANT_*``
value. The responding variants share the same I/O signature and defaults as their
non-responding counterparts; registering the same class under both type codes keeps the
filter's own ``filter_type`` attribute faithful to what the fish side expects while
avoiding duplicated subclass bodies.

The v-filter :attr:`FilterTypeEnumeration.VFILTER_POSITION_CONSTANT` (pan/tilt) is left in
the virtual-filters hierarchy; it has configuration-dependent terminals and is migrated in
the dynamic-terminal PR.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_CONSTANT_8BIT)
@register_filter(FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT)
class Constant8Bit(StaticIOMixin, Filter):
    """8-bit constant value exposed as a single output."""

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_8_BIT}
    GUI_UPDATE_KEYS: ClassVar[dict[str, DataType | list[str]]] = {"value": DataType.DT_8_BIT}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {"value": "0"}


@register_filter(FilterTypeEnumeration.FILTER_CONSTANT_16_BIT)
@register_filter(FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_16BIT)
class Constant16Bit(StaticIOMixin, Filter):
    """16-bit constant value exposed as a single output."""

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}
    GUI_UPDATE_KEYS: ClassVar[dict[str, DataType | list[str]]] = {"value": DataType.DT_16_BIT}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {"value": "0"}


@register_filter(FilterTypeEnumeration.FILTER_CONSTANT_FLOAT)
@register_filter(FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_FLOAT)
class ConstantFloat(StaticIOMixin, Filter):
    """Float constant value exposed as a single output."""

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}
    GUI_UPDATE_KEYS: ClassVar[dict[str, DataType | list[str]]] = {"value": DataType.DT_DOUBLE}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {"value": "0.0"}


@register_filter(FilterTypeEnumeration.FILTER_CONSTANT_COLOR)
@register_filter(FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_COLOR)
class ConstantColor(StaticIOMixin, Filter):
    """HSI colour constant exposed as a single colour output.

    The value is stored as the comma-separated ``"h,s,i"`` string accepted by
    :meth:`model.color_hsi.ColorHSI.from_filter_str`.
    """

    OUT: ClassVar[dict[str, DataType]] = {"value": DataType.DT_COLOR}
    GUI_UPDATE_KEYS: ClassVar[dict[str, DataType | list[str]]] = {"value": DataType.DT_COLOR}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {"value": "0,0,0"}
