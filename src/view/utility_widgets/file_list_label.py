"""Contains a label displaying primary file name and path."""
from __future__ import annotations

import os
from typing import override, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QColor
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QStyledItemDelegate, QStyle

if TYPE_CHECKING:
    from PySide6.QtGui import QPainter
    from PySide6.QtWidgets import QStyleOptionViewItem
    from PySide6.QtCore import QModelIndex


class FileListLabel(QWidget):
    """Displays primary file name and path."""

    def __init__(self, path: str, parent: QWidget | None = None) -> None:
        """Initializes the label for the given path."""
        super().__init__(parent)
        layout = QVBoxLayout()
        file_layout = QHBoxLayout()
        primary_file_name, extension = os.path.splitext(os.path.basename(path))
        primary_label = QLabel(primary_file_name)
        primary_label.setStyleSheet("font-weight: bold; font-size: large;")
        file_layout.addWidget(primary_label)
        file_layout.addWidget(QLabel(extension))
        file_layout.addStretch()
        layout.addLayout(file_layout)
        layout.addWidget(QLabel(path))
        self.setLayout(layout)


class FileListLabelDelegate(QStyledItemDelegate):
    """Delegate for displaying primary file name and path."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the delegate."""
        super().__init__(parent)
        self._color_background = QColor(64, 64, 64)
        self._color_selected = QColor(64, 64, 100)

    @override
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex, /):
        sh = super().sizeHint(option, index)
        sh.setHeight(sh.height() * 3)
        return sh

    @override
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex, /) -> None:
        path = index.data(Qt.ItemDataRole.DisplayRole)
        rect = option.rect
        x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()
        primary_file_name, extension = os.path.splitext(os.path.basename(path))
        painter.save()
        painter.fillRect(x, y, w, h,
                         self._color_selected if option.state & QStyle.State_Selected else self._color_background)

        font = painter.font()
        font.setPixelSize(20)
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        y += fm.height()
        painter.drawText(x, y, primary_file_name)
        x += fm.horizontalAdvance(primary_file_name)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(x, y, extension)

        x = rect.left()
        font.setPixelSize(14)
        fm = QFontMetrics(font)
        y += fm.height()
        painter.setFont(font)
        painter.drawText(x, y, path)
        painter.restore()
