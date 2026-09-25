"""Contains shared functionality for using OpenGL."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PySide6 import QtGui

logger = getLogger(__name__)

TranslateOp = tuple[str, tuple[float, float, float]]
RotateOp = tuple[str, tuple[float, float, float, float, float, float, float]]
LocalOp = TranslateOp | RotateOp


def _apply_local_ops(matrix: QtGui.QMatrix4x4, ops: Sequence[LocalOp]) -> None:
    """Apply a sequence of local transform operations to a matrix.

    Supported operations:
        ("translate", (x, y, z))
        ("rotate", (degrees, ax, ay, az, pivot_x, pivot_y, pivot_z))
    """
    for op in ops or ():
        if not op:
            continue
        name, payload = op[0], op[1]
        if name == "translate" and len(payload) == 3:
            x, y, z = payload
            matrix.translate(x, y, z)
        elif name == "rotate" and len(payload) == 7:
            deg, ax, ay, az, px, py, pz = payload
            matrix.translate(px, py, pz)
            matrix.rotate(deg, ax, ay, az)
            matrix.translate(-px, -py, -pz)
        else:
            logger.warning("Ignoring unknown or malformed local op: %r", op)
