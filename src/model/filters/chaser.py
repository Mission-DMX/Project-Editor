"""Colour chaser filter subclass.

Dynamic I/O: inputs come from the colon-separated ``number_parameters`` and
``color_parameters`` configuration strings; outputs are one DT_COLOR terminal per pixel as
declared by ``number_of_pixels``.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = getLogger(__name__)


@register_filter(FilterTypeEnumeration.FILTER_COLOR_CHASER)
class ColorChaser(StaticIOMixin, Filter):
    """Colour chaser filter.

    Always exposes ``time`` and ``time_scale`` float inputs. ``number_parameters`` names a
    colon-separated list of 16-bit input channels, ``color_parameters`` the same for colour
    channels. Each ``number_of_pixels`` pixel yields one colour output named by index.
    """

    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {
        "number_of_pixels": "1",
        "color_parameters": "",
        "number_parameters": "",
        "presets": "",
        "trigger_event": "",
    }
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {"config": ""}

    def _rebuild_io(self) -> None:
        """Apply defaults and derive dynamic inputs / outputs from configuration."""
        super()._rebuild_io()
        self._in_data_types["time"] = DataType.DT_DOUBLE
        self._in_data_types["time_scale"] = DataType.DT_DOUBLE
        self._default_values["time_scale"] = "1.0"

        for name in self._iter_names("number_parameters"):
            self._in_data_types[name] = DataType.DT_16_BIT
            self._default_values[name] = "0"

        for name in self._iter_names("color_parameters"):
            self._in_data_types[name] = DataType.DT_COLOR
            self._default_values[name] = "360.0,1.0,1.0"

        raw_pixels = self._filter_configurations.get("number_of_pixels", "1")
        try:
            pixel_count = int(raw_pixels)
        except ValueError:
            logger.warning(
                "ColorChaser %s: malformed number_of_pixels %r, resetting to 0",
                self._filter_id, raw_pixels,
            )
            pixel_count = 0
            self._filter_configurations["number_of_pixels"] = "0"
        if pixel_count < 0:
            pixel_count = 0
        for i in range(pixel_count):
            self._out_data_types[str(i)] = DataType.DT_COLOR

    def _iter_names(self, config_key: str) -> Iterator[str]:
        """Yield non-empty channel names from a colon-separated configuration entry."""
        raw = self._filter_configurations.get(config_key, "")
        if not raw:
            return
        for name in raw.split(":"):
            if name:
                yield name
