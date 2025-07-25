from typing import override

from PySide6 import QtGui
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from view.show_mode.editor.node_editor_widgets.cue_editor.view_settings import CHANNEL_DISPLAY_HEIGHT


class TimelineChannelLabel(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)
        self._names: list[str] = []
        self._types: list[str] = []
        self.setMinimumWidth(2 * CHANNEL_DISPLAY_HEIGHT)
        self.setMinimumHeight(20)
        self.sb_offset = 0
        self._update()

    def add_label(self, name: str, channel_type: str) -> None:
        self._names.append(name)
        self._types.append(channel_type)
        self._update()

    def remove_label(self, c_name: str) -> int:
        found_i = -1
        for i in range(len(self._names)):
            if self._names[i] == c_name:
                self._names.pop(i)
                self._types.pop(i)
                found_i = i
                break
        self._update()
        return found_i

    def clear_labels(self) -> None:
        self._names.clear()
        self._types.clear()
        self._update()

    def _update(self) -> None:
        required_height = 2 * 20 + CHANNEL_DISPLAY_HEIGHT * len(self._names) + self.sb_offset
        self.setMinimumHeight(required_height)
        self.update()

    @override
    def paintEvent(self, ev: QPaintEvent) -> None:
        w = self.width()
        h = self.height()
        if w == 0 or h == 0:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, w, h, QColor.fromRgb(0x3A, 0x3A, 0x3A))

        channel_background_color = QColor.fromRgb(0x4A, 0x4A, 0x4A)
        for i, channel_name in enumerate(self._names):
            if (i % 2) == 0:
                painter.fillRect(0, 20 + i * CHANNEL_DISPLAY_HEIGHT, w, CHANNEL_DISPLAY_HEIGHT,
                                 channel_background_color)
            painter.drawText(5, 45 + i * CHANNEL_DISPLAY_HEIGHT, channel_name)
            if len(self._types) > i:
                painter.drawText(10, 60 + i * CHANNEL_DISPLAY_HEIGHT, self._types[i])
        painter.end()
