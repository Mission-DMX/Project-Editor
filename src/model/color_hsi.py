"""Color in HSI Form."""

from __future__ import annotations

import colorsys
from typing import TYPE_CHECKING

import numpy as np
from PySide6.QtGui import QColor

if TYPE_CHECKING:
    from pydantic import confloat


class ColorHSI:
    """Color Definition."""

    def __init__(
        self, hue: confloat(ge=0, le=360), saturation: confloat(ge=0, le=1), intensity: confloat(ge=0, le=1)
    ) -> None:
        """HSI color.

        Args:
            hue: Color itself in the form of an angle between [0, 360] degrees.
            saturation: Value in the range [0, 1].
            intensity: Value in the range [0, 1], where 0 is black and 1 is white.

        """
        self._hue: confloat(ge=0, le=360) = hue
        self._saturation: confloat(ge=0, le=1) = saturation
        self._intensity: confloat(ge=0, le=1) = intensity

    @classmethod
    def from_filter_str(cls, filter_format: str) -> ColorHSI:
        """Initialize an HSI color from the given filter configuration string.

        Args:
        filter_format: The color provided as a filter configuration string.

        """
        if not filter_format or filter_format.count(",") < 2:
            return ColorHSI(128.0, 0.5, 1.0)
        parts = filter_format.split(",")
        if len(parts) < 3:
            raise ValueError("Expected HSI format: hue,saturation,intensity")
        hue = float(parts[0]) % 360.0
        saturation = float(parts[1])
        if saturation < 0:
            saturation = 0.0
        elif saturation > 1:
            saturation = 1.0
        intensity = float(parts[2])
        if intensity < 0:
            intensity = 0.0
        elif intensity > 1:
            intensity = 1.0
        return ColorHSI(hue, saturation, intensity)

    @classmethod
    def from_rgb(cls, red: int, green: int, blue: int) -> ColorHSI:
        """Initialize an HSI color from the given RGB color.

        Args:
            red: Red component of the color. It must be in the range [0, 255]
            green: Green component of the color. It must be in the range [0, 255]
            blue: Blue component of the color. It must be in the range [0, 255]

        Returns:
            The HSI color object.

        """
        hue, luminescence, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
        return ColorHSI(hue, luminescence, saturation)

    @classmethod
    def from_color_temperature(cls, temperature: float | str) -> ColorHSI:
        """Initialize an HSI color from the given color temperature.

        If a string is provided it will be converted automatically.

        Args:
            temperature: Color temperature in degrees Kelvin.

        Returns:
            A ColorHSI object representing the given color temperature.

        """

        def cutoff(value: float, min_val: int, max_val: int) -> int:
            return max(min(int(value), max_val), min_val)

        if isinstance(temperature, str):
            temperature = float(temperature.lower().replace(" ", "").replace("k", ""))
        temperature = temperature / 100
        if temperature <= 66:
            red = 255
            green = temperature
            green = 99.4708025861 * np.log(green) - 161.1195681661
            if temperature <= 19:
                blue = 0
            else:
                blue = temperature - 10
                blue = 138.5177312231 * np.log(blue) - 305.0447927307
        else:
            red = temperature - 60
            red = 329.698727446 * (red ** -0.1332047592)
            green = temperature - 60
            green = 288.1221695283 * (green ** -0.0755148492)
            blue = 255
        red = cutoff(red, 0, 255)
        green = cutoff(green, 0, 255)
        blue = cutoff(blue, 0, 255)
        return ColorHSI.from_rgb(red, green, blue)

    @property
    def hue(self) -> confloat(ge=0, le=360):
        """Color itself in the form of an angle between [0,360] degrees."""
        return self._hue

    @property
    def saturation(self) -> confloat(ge=0, le=1):
        """Saturation of the color.

        Float between (including) zero (100% white, 0% color) and 1 (0% white, 100% color).
        """
        return self._saturation

    @property
    def intensity(self) -> confloat(ge=0, le=1):
        """Perceived illuminance.

        float [0, 1] where 0 is black, and 1 is white.
        """
        return self._intensity

    def format_for_filter(self) -> str:
        """Format the color so it can be parsed by fish filters."""
        return f"{float(self._hue)},{float(self._saturation)},{float(self._intensity)}"

    def to_rgb(self) -> tuple[int, int, int]:
        """RGB representations as int between 0 and 255."""
        rr, rg, rb = colorsys.hsv_to_rgb((self._hue % 360) / 360.0, self._saturation, self._intensity)
        return int(rr * 255), int(rg * 255), int(rb * 255)

    def to_qt_color(self) -> QColor:
        """Return color in qt color format."""
        return QColor.fromHsvF((self._hue % 360.0) / 360.0, self._saturation, self._intensity)

    def copy(self) -> ColorHSI:
        """Return a copy of The color object."""
        return ColorHSI(self._hue, self._saturation, self._intensity)

    @classmethod
    def from_qt_color(cls, c: QColor) -> ColorHSI:
        """Generate a HSI color from qt color format."""
        return ColorHSI(c.hsvHueF() * 360.0, c.hsvSaturationF(), c.lightnessF())

    def __str__(self) -> str:
        """Format color as HTML color code."""
        r, g, b = self.to_rgb()
        return f"#{r:02x}{g:02x}{b:02x}".upper()
