"""patch Plan Widget for one Universe"""

from typing import Final, override

from PySide6.QtGui import QColorConstants, QPainter, QPixmap, QResizeEvent
from PySide6.QtWidgets import QGraphicsView, QStyleOptionGraphicsItem, QWidget

from model.universe import NUMBER_OF_CHANNELS
from view.patch_view.patch_plan.channel_item_generator import (
    channel_item_height,
    channel_item_spacing,
    channel_item_width,
    create_item,
)
from view.patch_view.patch_plan.patch_base_item import PatchBaseItem


class AutoResizeView(QGraphicsView):
    """View, automatically resizes scene."""

    _base_item = PatchBaseItem()

    @override
    def resizeEvent(self, event: QResizeEvent, /) -> None:
        """Resize the View."""
        super().resizeEvent(event)
        new_width = self.viewport().width()
        self._base_item.resize(new_width)
        self.setSceneRect(0, 0, new_width, self._base_item.boundingRect().height())


class PatchPlanWidget(PatchBaseItem):
    """Patch Plan Widget for one Universe."""

    _background_tiles: Final[list[QPixmap]] = [
        create_item(i + 1, QColorConstants.White) for i in range(NUMBER_OF_CHANNELS)
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setZValue(-10)

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, /, widget: QWidget | None = ...) -> None:
        for i, channel_item in enumerate(self._background_tiles):
            x = (i % self._cols) * (channel_item_width() + channel_item_spacing())
            y = (i // self._cols) * (channel_item_height() + channel_item_spacing())
            painter.drawPixmap(x, y, channel_item)
