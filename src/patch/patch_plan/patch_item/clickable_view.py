"""Clickable overview."""

from typing import override

from PySide6 import QtCore
from PySide6.QtGui import QColor, QPainter, QPixmap, Qt
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, QWidget

import style
from model.universe import NUMBER_OF_CHANNELS
from patch.patch_plan.patch_base_item import PatchBaseItem


def create_click_item(active: bool) -> QPixmap:
    """Create a pixmap of a Channel item."""
    pixmap = QPixmap(style.PATCH_ITEM.width, style.PATCH_ITEM.height)
    pixmap.fill(Qt.transparent)
    if active:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(0, 120, 255, 100)  # RGB + Transparenz
        painter.fillRect(0, 0, style.PATCH_ITEM.width - 1, style.PATCH_ITEM.height - 1, color)
        painter.end()

    return pixmap


class ClickableView(PatchBaseItem):
    """Clickable overview."""

    click_channel = QtCore.Signal(int, int)
    _active_channel = create_click_item(True)
    _inactive_channel = create_click_item(False)

    def __init__(self) -> None:
        """Patch Plan Widget for one Universe."""
        super().__init__()
        self._clicked = set()
        self.setZValue(20)

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, /, widget: QWidget | None = ...) -> None:
        for i in range(NUMBER_OF_CHANNELS):
            x = (i % self._cols) * (style.PATCH_ITEM.width + style.PATCH_ITEM.margin)
            y = (i // self._cols) * (style.PATCH_ITEM.height + style.PATCH_ITEM.margin)
            if i in self._clicked:
                painter.drawPixmap(x, y, self._active_channel)
            else:
                painter.drawPixmap(x, y, self._inactive_channel)

    @override
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        x = event.pos().x()
        y = event.pos().y()

        col = int(x // (style.PATCH_ITEM.width + style.PATCH_ITEM.margin))
        row = int(y // (style.PATCH_ITEM.height + style.PATCH_ITEM.margin))
        index = row * self._cols + col

        if index in self._clicked:
            self._clicked.remove(index)
            self.click_channel.emit(index, 0)
        else:
            self._clicked.add(index)
            self.click_channel.emit(index, 255)

        super().mousePressEvent(event)
        self.update()
