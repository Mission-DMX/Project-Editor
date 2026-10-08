"""Debug filter subclasses.

Local (``FILTER_DEBUG_OUTPUT_*``) and remote (``FILTER_REMOTE_DEBUG_*``) debug outputs share
one subclass per data type; stacked ``@register_filter`` decorators register each class
under both type codes so filters constructed with either code land on the right signature
while retaining their original ``filter_type`` for fish.

All debug filters have a single ``value`` input and no outputs.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_8BIT)
@register_filter(FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT)
class Debug8Bit(StaticIOMixin, Filter):
    """Debug sink for an 8-bit value."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_8_BIT}


@register_filter(FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_16BIT)
@register_filter(FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT)
class Debug16Bit(StaticIOMixin, Filter):
    """Debug sink for a 16-bit value."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_16_BIT}


@register_filter(FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_FLOAT)
@register_filter(FilterTypeEnumeration.FILTER_REMOTE_DEBUG_FLOAT)
class DebugFloat(StaticIOMixin, Filter):
    """Debug sink for a float/double value."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_DOUBLE}


@register_filter(FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_COLOR)
@register_filter(FilterTypeEnumeration.FILTER_REMOTE_DEBUG_PIXEL)
class DebugColor(StaticIOMixin, Filter):
    """Debug sink for a colour value (local output or remote pixel)."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    IN: ClassVar[dict[str, DataType]] = {"value": DataType.DT_COLOR}
