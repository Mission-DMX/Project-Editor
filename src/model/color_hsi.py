# coding=utf-8
"""Color in HSI Form"""
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
