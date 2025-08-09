"""QGraphicsItem for patching items."""

import math
from typing import override

from PySide6.QtCore import QObject, QRectF
from PySide6.QtWidgets import QGraphicsItem

import style
from model.universe import NUMBER_OF_CHANNELS


class PatchBaseItem(QObject, QGraphicsItem):
    """QGraphicsItem for patching items."""

    _cols = 1
    _rows = 1
    _view_width = 100

    def __init__(self) -> None:
        """Initialize."""
        QObject.__init__(self)
        QGraphicsItem.__init__(self)

    @classmethod
    def resize(cls, view_width: int) -> None:
        """Handle resize the view."""
        cls._view_width = view_width
        new_cols = max(1, cls._view_width // (style.PATCH_ITEM.width + style.PATCH_ITEM.margin))
        if new_cols != cls._cols:
            cls._cols = new_cols
            cls._rows = math.ceil(NUMBER_OF_CHANNELS / new_cols)

    @override
    def boundingRect(self) -> QRectF:
        """Bounding rectangle of this item."""
        return QRectF(0, 0, self._view_width, self._rows * (style.PATCH_ITEM.height + style.PATCH_ITEM.margin))
