"""Fader filter subclasses.

Covers the five column-fader variants (raw / HSI / HSI-A / HSI-U / HSI-AU) and the global
main-brightness fader. These are output-only filters with their type-specific out ports and
a shared ``set_id`` / ``column_id`` configuration pointing at a desk control-column.

The HSI variants additionally expose ``ignore_main_brightness_control`` as a configuration
knob (defaults to ``"false"``).

Node-layer concerns — BankSet listener subscription and lifecycle — remain in
:mod:`view.show_mode.editor.nodes.impl.faders`.
"""

from __future__ import annotations

from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter

_FADER_BASE_CONFIGS: dict[str, str] = {"set_id": "", "column_id": ""}
_HSI_FADER_CONFIGS: dict[str, str] = {**_FADER_BASE_CONFIGS, "ignore_main_brightness_control": "false"}


class _FaderBase(StaticIOMixin, Filter):
    """Shared configuration defaults for the column-fader filters."""

    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = _FADER_BASE_CONFIGS


@register_filter(FilterTypeEnumeration.FILTER_FADER_RAW)
class FaderRaw(_FaderBase):
    """Raw column fader exposing two 16-bit outputs (primary and secondary)."""

    OUT: ClassVar[dict[str, DataType]] = {
        "primary": DataType.DT_16_BIT,
        "secondary": DataType.DT_16_BIT,
    }


@register_filter(FilterTypeEnumeration.FILTER_FADER_HSI)
class FaderHSI(_FaderBase):
    """HSI colour-column fader exposing a single colour output."""

    OUT: ClassVar[dict[str, DataType]] = {"color": DataType.DT_COLOR}
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = _HSI_FADER_CONFIGS


@register_filter(FilterTypeEnumeration.FILTER_FADER_HSIA)
class FaderHSIA(_FaderBase):
    """HSI + Amber colour-column fader (``color`` + 8-bit ``amber``)."""

    OUT: ClassVar[dict[str, DataType]] = {"color": DataType.DT_COLOR, "amber": DataType.DT_8_BIT}
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = _HSI_FADER_CONFIGS


@register_filter(FilterTypeEnumeration.FILTER_FADER_HSIU)
class FaderHSIU(_FaderBase):
    """HSI + UV colour-column fader (``color`` + 8-bit ``uv``)."""

    OUT: ClassVar[dict[str, DataType]] = {"color": DataType.DT_COLOR, "uv": DataType.DT_8_BIT}
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = _HSI_FADER_CONFIGS


@register_filter(FilterTypeEnumeration.FILTER_FADER_HSIAU)
class FaderHSIAU(_FaderBase):
    """HSI + Amber + UV colour-column fader."""

    OUT: ClassVar[dict[str, DataType]] = {
        "color": DataType.DT_COLOR,
        "amber": DataType.DT_8_BIT,
        "uv": DataType.DT_8_BIT,
    }
    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = _HSI_FADER_CONFIGS


@register_filter(FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS)
class MainBrightness(StaticIOMixin, Filter):
    """Global master-brightness fader exposing a single 16-bit output."""

    CONFIGURATION_SUPPORTED: ClassVar[bool] = False
    OUT: ClassVar[dict[str, DataType]] = {"brightness": DataType.DT_16_BIT}
