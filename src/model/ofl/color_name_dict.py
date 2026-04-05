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
    """This method queries the color name database and returns black if none was found."""
    color_tuple = _COLOR_DICT.get(name.lower())
    if color_tuple is not None:
        return ColorHSI(color_tuple[0], color_tuple[1], color_tuple[2])
    logger.warning("No color name found for %s", name)
    return ColorHSI(0, 0, 0)
