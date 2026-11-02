"""Signal-routing filter subclasses (switch variants).

Each ``FILTER_SWITCH_*`` filter forwards one of ``nr_inputs`` typed input channels
(named ``"0"``, ``"1"``, ...) to a single ``out`` output of the same type, under the
control of a 16-bit ``select`` input.

Also fixes a latent bug: the previous view-side implementation stored the output's data
type under ``in_data_types["out"]`` instead of ``out_data_types["out"]``, which broke the
editor's downstream-connection type check.
"""

from __future__ import annotations

from logging import getLogger
from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter

logger = getLogger(__name__)

class _SwitchBase(StaticIOMixin, Filter):
    """Shared logic for the ``FILTER_SWITCH_*`` native filters.

    Subclasses declare their forwarded data type via ``_DT``. The ``select`` input is always
    a 16-bit value (default ``"0"``); the number of selectable inputs comes from
    ``filter_configurations["nr_inputs"]`` (default ``"2"``).
    """

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"nr_inputs": "2"}

    def _rebuild_io(self) -> None:
        """Apply defaults and derive input / output signatures from ``nr_inputs``."""
        super()._rebuild_io()
        dt = type(self)._DT
        self._out_data_types["out"] = dt
        self._in_data_types["select"] = DataType.DT_16_BIT
        self._default_values["select"] = "0"
        raw_count = self._filter_configurations.get("nr_inputs", "2")
        try:
            count = int(raw_count)
        except ValueError:
            logger.error("Failed to parse %s as number of inputs. Resetting filter with ID %s to 0.",
                         self._filter_configurations.get("nr_inputs"), self._filter_id)
            count = 0
            self._filter_configurations["nr_inputs"] = "0"
        if count < 0:
            count = 0
        default = "0,0,0" if dt == DataType.DT_COLOR else "0"
        for i in range(count):
            name = str(i)
            self._in_data_types[name] = dt
            self._default_values[name] = default


@register_filter(FilterTypeEnumeration.FILTER_SWITCH_8BIT)
class Switch8Bit(_SwitchBase):
    """Switch between a configurable number of 8-bit inputs."""

    _DT: ClassVar[DataType] = DataType.DT_8_BIT


@register_filter(FilterTypeEnumeration.FILTER_SWITCH_16BIT)
class Switch16Bit(_SwitchBase):
    """Switch between a configurable number of 16-bit inputs."""

    _DT: ClassVar[DataType] = DataType.DT_16_BIT


@register_filter(FilterTypeEnumeration.FILTER_SWITCH_FLOAT)
class SwitchFloat(_SwitchBase):
    """Switch between a configurable number of float inputs."""

    _DT: ClassVar[DataType] = DataType.DT_DOUBLE


@register_filter(FilterTypeEnumeration.FILTER_SWITCH_COLOR)
class SwitchColor(_SwitchBase):
    """Switch between a configurable number of colour inputs."""

    _DT: ClassVar[DataType] = DataType.DT_COLOR
