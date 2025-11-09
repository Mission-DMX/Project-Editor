"""Clickable overview."""

from typing import override

from PySide6 import QtCore
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap, Qt
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsProxyWidget,
    QGraphicsSceneMouseEvent,
    QGraphicsSimpleTextItem,
    QSlider,
    QStyleOptionGraphicsItem,
    QWidget,
)

import style
from model.universe import NUMBER_OF_CHANNELS
from patch.patch_plan.patch_base_item import PatchBaseItem


def create_click_item(active: bool) -> QPixmap:
    """Create a pixmap of a Channel item."""
    pixmap = QPixmap(style.PATCH_ITEM.width, style.PATCH_ITEM.height)
    pixmap.fill(Qt.GlobalColor.transparent)
    if active:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(0, 120, 255, 100)  # RGB + Transparenz
        painter.fillRect(0, 0, style.PATCH_ITEM.width - 1, style.PATCH_ITEM.height - 1, color)
        painter.end()

    return pixmap


class ClickableView(PatchBaseItem):
    """Clickable overview."""

    channel_value_change = QtCore.Signal(int, int)
    _active_channel = create_click_item(True)
    _inactive_channel = create_click_item(False)

    def __init__(self) -> None:
        """Patch Plan Widget for one Universe."""
        super().__init__()
        self._clicked = set()
        self.setZValue(20)
        self._double_click = False
        self._slider_proxies = {}

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
        """Catch mouse press events."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.pos().x()
        y = event.pos().y()

        QTimer.singleShot(QApplication.doubleClickInterval(), lambda: self._handle_click(x, y))

    def _handle_click(self, x: float, y: float) -> None:
        """Handle mouse click."""
        if self._double_click:
            self._double_click = False
            return

        col = int(x // (style.PATCH_ITEM.width + style.PATCH_ITEM.margin))
        row = int(y // (style.PATCH_ITEM.height + style.PATCH_ITEM.margin))
        index = row * self._cols + col

        if index in self._slider_proxies:
            return

        if index in self._clicked:
            self._clicked.remove(index)
            self.channel_value_change.emit(index, 0)
        else:
            self._clicked.add(index)
            self.channel_value_change.emit(index, 255)

        self.update()

    @override
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent, /) -> None:
        """Handle mouse double click."""
        self._double_click = True
        x = event.pos().x()
        y = event.pos().y()
        col = int(x // (style.PATCH_ITEM.width + style.PATCH_ITEM.margin))
        row = int(y // (style.PATCH_ITEM.height + style.PATCH_ITEM.margin))
        index = row * self._cols + col

        if index in self._slider_proxies:
            for item in self._slider_proxies[index]:
                self.scene().removeItem(item)
            self._slider_proxies.pop(index)
            return

        if index in self._clicked:
            self._clicked.remove(index)
            self.channel_value_change.emit(index, 0)

        slider = QSlider(QtCore.Qt.Orientation.Vertical)
        slider.setRange(0, 255)
        slider.setSingleStep(1)
        slider.setFixedHeight(style.PATCH_ITEM.height)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(slider)

        x = col * (style.PATCH_ITEM.width + style.PATCH_ITEM.margin) + style.PATCH_ITEM.width - slider.width()
        y = row * (style.PATCH_ITEM.height + style.PATCH_ITEM.margin)

        proxy.setPos(x, y)
        label = QGraphicsSimpleTextItem(str(slider.value()), self)
        label.setPos(proxy.pos().x() - 35, proxy.pos().y() + style.PATCH_ITEM.height - 20)
        slider.valueChanged.connect(lambda value: self.update_value(index, value, label))

        self._slider_proxies.update({index: [proxy, label]})

        event.accept()

    def update_value(self, index: int, value: int, text: QGraphicsSimpleTextItem) -> None:
        """Update of a value in."""
        self.channel_value_change.emit(index, value)
        text.setText(str(value))
