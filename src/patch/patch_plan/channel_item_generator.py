"""Channel items of the Patching."""

from PySide6.QtGui import QColor, QColorConstants, QPainter, QPixmap

import style


def create_item(number: int, color: QColor) -> QPixmap:
    """Create a pixmap of a Channel item."""
    pixmap = QPixmap(style.PATCH_ITEM.width, style.PATCH_ITEM.height)
    pixmap.fill(color)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(QColorConstants.Black)
    painter.drawRect(0, 0, style.PATCH_ITEM.width - 1, style.PATCH_ITEM.height - 1)

    paint_text(painter, style.PATCH_ITEM.parts.channel_id, style.PATCH_ITEM.padding, str(number))
    painter.end()

    return pixmap


def paint_text(painter: QPainter, text_style: style._TextItem, offset: int | tuple[int, int], text: str) -> None:
    """Paint text."""
    if type(offset) is int:
        offset = [offset, offset]
    painter.setFont(text_style.font)
    painter.drawText(
        offset[0] + text_style.x,
        offset[1] + text_style.y,
        text,
    )
