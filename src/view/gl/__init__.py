"""Contains shared functionality for using OpenGL."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6 import QtGui


def _apply_local_ops(matrix: QtGui.QMatrix4x4, ops:
list[tuple[str, tuple[float, float, float] | tuple[float, float, float, float, float, float]]]) -> None:
    """Apply a sequence of local transform operations to a matrix.

    Supported operations:
        ("translate", (x, y, z))
        ("rotate", (degrees, ax, ay, az, pivot_x, pivot_y, pivot_z))
    """
    for op in ops or ():
        if not op:
            continue
        name, payload = op[0], op[1]
        if name == "translate":
            matrix.translate(*payload)
        elif name == "rotate":
            deg, ax, ay, az, px, py, pz = payload
            matrix.translate(px, py, pz)
            matrix.rotate(deg, ax, ay, az)
            matrix.translate(-px, -py, -pz)
