"""Patch Plan Widget for one Universe."""

from typing import Final, override

from PySide6.QtGui import QColorConstants, QPainter, QPixmap
from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget

import style
from model.universe import NUMBER_OF_CHANNELS
from patch.patch_plan.channel_item_generator import (
    create_item,
)
from patch.patch_plan.patch_base_item import PatchBaseItem


class BackgroundView(PatchBaseItem):
    """Patch Plan Widget for one Universe."""

    _background_tiles: Final[list[QPixmap]] = [
        create_item(i + 1, QColorConstants.White) for i in range(NUMBER_OF_CHANNELS)
    ]

    def __init__(self) -> None:
        """Patch Plan Widget for one Universe."""
        super().__init__()
        self.setZValue(-10)

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, /, widget: QWidget | None = ...) -> None:
        for i, channel_item in enumerate(self._background_tiles):
            x = (i % self._cols) * (style.PATCH_ITEM.width + style.PATCH_ITEM.margin)
            y = (i // self._cols) * (style.PATCH_ITEM.height + style.PATCH_ITEM.margin)
            painter.drawPixmap(x, y, channel_item)
