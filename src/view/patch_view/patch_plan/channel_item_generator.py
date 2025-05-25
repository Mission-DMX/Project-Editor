# coding=utf-8
""" item of the Patching """
from PySide6.QtGui import QPixmap, QColorConstants, QPainter, QFont

_width = 100
_height = 100


def item_width():
    """width of the item"""
    return _width


def item_height():
    """height of the item"""
    return _height


def create_item(number, color=QColorConstants.White) -> QPixmap:
    """creates a pixmap of the item"""
    pixmap = QPixmap(_width, _height)
    pixmap.fill(color)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(QColorConstants.Black)
    painter.drawRect(0, 0, _width - 1, _height - 1)

    font = QFont("Arial", 12)
    painter.setFont(font)
    painter.drawText(5, 20, str(number))
    painter.end()

    return pixmap
