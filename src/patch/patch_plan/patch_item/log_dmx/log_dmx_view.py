from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QColorConstants, QPainter, QPixmap, QPolygon, QTransform

import style
from patch.patch_plan.channel_item_generator import paint_text
from patch.patch_plan.patch_base_item import PatchBaseItem

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget

    from patch.patch_plan.patch_item.log_dmx.log_dmx_model import LogDmxModel


def _make_triangle_pixmap(width: int, height: int, color: QColor, rotation: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.GlobalColor.black)
    painter.setBrush(color)

    points = QPolygon([QPoint(0, 0), QPoint(width, 0), QPoint(width // 2, height)])
    painter.drawPolygon(points)
    painter.end()
    transform = QTransform().rotate(rotation)
    return pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)


# Statische Pixmap nur EINMAL erzeugen
TREND_UP_COLOR = QColorConstants.Blue
TREND_UP = _make_triangle_pixmap(
    style.PATCH_ITEM.parts.dmx_trend_icon.width, style.PATCH_ITEM.parts.dmx_trend_icon.height, TREND_UP_COLOR, 180
)
TREND_DOWN_COLOR = QColorConstants.Magenta
TREND_DOWN = _make_triangle_pixmap(
    style.PATCH_ITEM.parts.dmx_trend_icon.width,
    style.PATCH_ITEM.parts.dmx_trend_icon.height,
    TREND_DOWN_COLOR,
    0,
)
TREND_STAY_COLOR = QColorConstants.Black
TREND_STAY = _make_triangle_pixmap(
    style.PATCH_ITEM.parts.dmx_trend_icon.width,
    style.PATCH_ITEM.parts.dmx_trend_icon.height,
    QColorConstants.Black,
    270,
)


class LogDMXView(PatchBaseItem):
    def __init__(self, model: LogDmxModel) -> None:
        super().__init__()
        self.setZValue(10)
        self._model = model
        self._model.new_value.connect(self.update)

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, /, widget: QWidget | None = ...) -> None:
        """Paint the current DMX values."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for index, value in enumerate(self._model.current_values):
            painter.setPen(QColorConstants.Black)
            x_base = (index % self._cols) * (
                style.PATCH_ITEM.width + style.PATCH_ITEM.margin
            ) + style.PATCH_ITEM.padding
            y_base = (index // self._cols) * (
                style.PATCH_ITEM.height + style.PATCH_ITEM.margin
            ) + style.PATCH_ITEM.padding

            paint_text(painter, style.PATCH_ITEM.parts.dmx_value, (x_base, y_base), str(value))

            trend = self._model.trend(index)
            x = x_base + style.PATCH_ITEM.parts.dmx_trend_icon.x
            y = y_base + style.PATCH_ITEM.parts.dmx_trend_icon.y
            if trend == 0:
                painter.drawPixmap(x, y, TREND_STAY)
                painter.setPen(TREND_STAY_COLOR)
            elif trend > 0:
                painter.drawPixmap(x, y, TREND_UP)
                painter.setPen(TREND_UP_COLOR)
            else:
                painter.drawPixmap(x, y, TREND_DOWN)
                painter.setPen(TREND_DOWN_COLOR)

            paint_text(painter, style.PATCH_ITEM.parts.dmx_trend, (x_base, y_base), str(abs(trend)))
