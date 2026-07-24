"""Contains SpotLightData."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6 import QtGui


class SpotLightData:
    """Spotlight data collected per frame from active MovingHeads."""

    __slots__ = ("color", "direction", "inner_cos", "outer_cos", "position")

    def __init__(self,
                 position: QtGui.QVector3D,
                 direction: QtGui.QVector3D,
                 color: tuple[float, float, float],
                 inner_deg: float=10.0,
                 outer_deg: float=18.0) -> None:
        """Initialize struct."""
        self.position: QtGui.QVector3D = position      # QVector3D
        self.direction: QtGui.QVector3D = direction    # QVector3D (normalized)
        self.color: tuple[float, float, float] = color  # (r, g, b) floats in [0, 1]
        self.inner_cos: float = math.cos(math.radians(inner_deg))
        self.outer_cos: float = math.cos(math.radians(outer_deg))
