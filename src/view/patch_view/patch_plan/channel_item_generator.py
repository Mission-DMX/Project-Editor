""" item of the Patching """
from PySide6.QtGui import QColor, QColorConstants, QFont, QPainter, QPixmap

_WIDTH = 100
_HEIGHT = 100


def item_width():
    """width of the item"""
    return _WIDTH


def item_height():
    """height of the item"""
    return _HEIGHT


def create_item(number:int, color: QColor = QColorConstants.White) -> QPixmap:
    """creates a pixmap of the item"""
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
