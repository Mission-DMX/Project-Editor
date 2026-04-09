import csv
import os
from logging import getLogger
from typing import TYPE_CHECKING

from model.color_hsi import ColorHSI
from utility import resource_path

logger = getLogger(__name__)
_COLOR_DICT: dict[str, tuple[float, float, float]] = {}

with open(resource_path(os.path.join("resources", "data", "colornames.csv")), "r") as f:
    for row in csv.reader(f, delimiter=";"):
        name, hue, saturation, value = row
        _COLOR_DICT[name.lower()] = (float(hue), float(saturation), float(value))

def get_color_by_name(name: str) -> ColorHSI:
    """This method queries the color name database and returns black if none was found.

    HTML color codes are supported.

    Args:
        name: The name or color code of the color.

    Returns:
        The inferred color object.

    """
    if name.startswith("#"):
        name = name.replace("#", "")
        r = int(name[0:2], 16)
        g = int(name[2:4], 16)
        b = int(name[4:6], 16)
        return ColorHSI.from_rgb(r, g, b)
    color_tuple = _COLOR_DICT.get(name.lower())
    if color_tuple is not None:
        return ColorHSI(color_tuple[0], color_tuple[1], color_tuple[2])
    logger.warning("No color name found for %s", name)
    return ColorHSI(0, 0, 0)
