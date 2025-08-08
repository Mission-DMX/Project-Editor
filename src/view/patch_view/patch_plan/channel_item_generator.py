"""Channel items of the Patching."""

from PySide6.QtGui import QColor, QColorConstants, QFont, QPainter, QPixmap

_WIDTH: int = 100
_HEIGHT: int = 100
_SPACING: int = 1


def channel_item_width() -> int:
    """Width of one Channel item."""
    return _WIDTH


def channel_item_height() -> int:
    """Height of one Channel item."""
    return _HEIGHT


def channel_item_spacing() -> int:
    """Spacing between two Channel items."""
    return _SPACING


def create_item(number: int, color: QColor) -> QPixmap:
    """Create a pixmap of a Channel item."""
    pixmap = QPixmap(_WIDTH, _HEIGHT)
    pixmap.fill(color)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(QColorConstants.Black)
    painter.drawRect(0, 0, _WIDTH - 1, _HEIGHT - 1)

    font = QFont("Arial", 12)
    painter.setFont(font)
    painter.drawText(5, 20, str(number))
    painter.end()

    return pixmap
