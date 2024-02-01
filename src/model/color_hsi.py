# coding=utf-8
"""Color in HSI Form"""
import colorsys

from PySide6.QtGui import QColor
from pydantic import confloat


class ColorHSI:
    """Color Definition"""

    def __init__(self, hue: confloat(ge=0, le=360), saturation: confloat(ge=0, le=1), intensity: confloat(ge=0, le=1)):
        """ HSI Color
        Args:
            hue: color itself in the form of an angle between [0,360] degrees
            saturation:  in range of [0,1]
            intensity: in range of [0,1] where 0 is black and 1 is white

        """
        self._hue: confloat(ge=0, le=360) = hue
        self._saturation: confloat(ge=0, le=1) = saturation
        self._intensity: confloat(ge=0, le=1) = intensity

    @classmethod
    def from_filter_str(cls, filter_format: str):
        """ HSI Color

        This constructor parses the supplied color string and constructs the color object from it.

        Arguments:
            filter_format -- The color provided as a filter configuration string
        """
        if not filter_format or filter_format.count(",") < 2:
            return ColorHSI(128.0, 0.5, 1.0)
        parts = filter_format.split(",")
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

    @property
    def hue(self) -> confloat(ge=0, le=360):
        """color itself in the form of an angle between [0,360] degrees"""
        return self._hue

    @property
    def saturation(self) -> confloat(ge=0, le=1):
        """Saturation of the color.

        Float between (including) zero (100% white, 0% color) and 1 (0% white, 100% color)
        """
        return self._saturation

    @property
    def intensity(self) -> confloat(ge=0, le=1):
        """Perceived illuminance, float [0, 1]
        where 0 is black and 1 is white
        """
        return self._intensity

    def format_for_filter(self) -> str:
        """This method formats the color to be parsable by fish filters."""
        return f"{float(self._hue)},{float(self._saturation)},{float(self._intensity)}"

    def to_rgb(self) -> tuple[int, int, int]:
        """This method returns the RGB representations as int between 0 and 255"""
        rr, rg, rb = colorsys.hls_to_rgb((self._hue % 360) / 360.0, self._intensity, self._saturation)
        return int(rr * 255), int(rg * 255), int(rb * 255)

    def to_qt_color(self) -> QColor:
        return QColor.fromHslF((self._hue % 360.0) / 360.0, self._saturation, self._intensity)

    def copy(self) -> "ColorHSI":
        return ColorHSI(self._hue, self._saturation, self._intensity)

    @classmethod
    def from_qt_color(cls, c: QColor):
        return ColorHSI(c.hslHueF() * 360.0, c.hslSaturationF(), c.lightnessF())
