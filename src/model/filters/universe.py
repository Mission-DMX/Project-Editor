"""DMX universe output filter subclass.

Dynamic I/O: every ``filter_configurations`` key other than ``"universe"`` corresponds to a
DMX channel assignment and becomes an 8-bit input terminal. The ``"universe"`` entry stores
the universe id and does not surface as a terminal.
"""

from __future__ import annotations

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT)
class UniverseOutput(StaticIOMixin, Filter):
    """Universe output filter whose input terminals mirror its configuration."""

    def _rebuild_io(self) -> None:
        """Reset I/O to empty, then declare one 8-bit input per non-universe config key."""
        super()._rebuild_io()
        for key in self._filter_configurations:
            if key == "universe":
                continue
            self._in_data_types[key] = DataType.DT_8_BIT
            self._default_values[key] = "0"
