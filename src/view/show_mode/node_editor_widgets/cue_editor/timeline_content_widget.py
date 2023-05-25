import PySide6
from PySide6 import QtGui
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath
from PySide6.QtWidgets import QLabel, QWidget

from model import DataType
from model.control_desk import set_seven_seg_display_content
from view.show_mode.node_editor_widgets.cue_editor.cue import KeyFrame
from view.show_mode.node_editor_widgets.cue_editor.utility import format_seconds
from view.show_mode.node_editor_widgets.cue_editor.view_settings import CHANNEL_DISPLAY_HEIGHT


class TimelineContentWidget(QLabel):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self._last_keyframe_end_point = 0  # Defines the length of the Cue in seconds
        self._time_zoom = 0.01  # Defines how many seconds are a pixel, defaults to 1 pixel = 10ms
        self._channels = []
        self.frames: list[KeyFrame] = []
        self.cursor_position = 3.0
        self._drag_begin: tuple[int, int] = None
        self.compute_resize()
        self.cue_index: int = 0
        # TODO implement

    def repaint(self) -> None:
        canvas = self.pixmap()
        w = canvas.width()
        h = canvas.height()
        if w == 0 or h == 0:
            return
        painter = QtGui.QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)

        # Render background
        painter.fillRect(0, 0, w, h, QColor.fromRgb(0x3A, 0x3A, 0x3A))

        # render transitions
        i = 0
        channel_background_color = QColor.fromRgb(0x4A, 0x4A, 0x4A)
        for c in self._channels:
            if (i % 2) == 0:
                painter.fillRect(0, 20 + i * CHANNEL_DISPLAY_HEIGHT, w, CHANNEL_DISPLAY_HEIGHT,
                                 channel_background_color)
            i += 1

        marker_brush = QBrush(QColor.fromRgb(0xFF, 0xFF, 0x00))
        light_gray_brush = QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC))
        painter.setBrush(light_gray_brush)
        for kf in self.frames:
            i = 0
            x = kf.timestamp / self._time_zoom
            for s in kf._states:
                y = 40 + i * CHANNEL_DISPLAY_HEIGHT
                marker_path = QPainterPath(QPoint(x, y))
                marker_path.lineTo(x + 10, y + 10)
                marker_path.lineTo(x, y + 20)
                marker_path.lineTo(x - 10, y + 10)
                marker_path.lineTo(x, y)
                painter.fillPath(marker_path, marker_brush)
                # TODO show color circle if color instead of text
                painter.drawText(x + 15, y + 10, s.encode())
                i += 1

        # render cursor and bars
        painter.setBrush(light_gray_brush)
        painter.drawLine(0, 20, w, 20)
        painter.drawLine(0, h - 20, w, h - 20)
        abs_cursor_pos = int(self.cursor_position / self._time_zoom)
        cursor_path = QPainterPath(QPoint(abs_cursor_pos, 0))
        cursor_path.moveTo(-16 + abs_cursor_pos, 0)
        cursor_path.lineTo(16 + abs_cursor_pos, 0)
        cursor_path.lineTo(1 + abs_cursor_pos, 20)
        cursor_path.lineTo(1 + abs_cursor_pos, h - 20)
        cursor_path.lineTo(-1 + abs_cursor_pos, h - 20)
        cursor_path.lineTo(-1 + abs_cursor_pos, 20)
        cursor_path.lineTo(-16 + abs_cursor_pos, 0)
        painter.fillPath(cursor_path, QBrush(QColor.fromRgb(0xFF, 0x2F, 0x2F)))

        # render timescale
        x = 0
        painter.setBrush(light_gray_brush)
        while x < w:
            painter.drawLine(x, h - 20, x, h)
            time_str = format_seconds(x * self._time_zoom)
            painter.drawText(x, h - 2, time_str)
            x += 10 * len(time_str)

        painter.end()
        self.setPixmap(canvas)

    def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        super().mousePressEvent(ev)
        self._drag_begin = (ev.x(), ev.y())
        self.repaint()

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        canvas = QtGui.QPixmap(event.size().width(), event.size().height())
        canvas.fill(Qt.black)
        self.setPixmap(canvas)
        self.repaint()

    def compute_resize(self):
        p = self.parent()
        if p:
            parent_height = p.height()
            parent_width = p.width()
        else:
            parent_height = 150
            parent_width = 150
        self.setMinimumWidth(max(parent_width, int(self._last_keyframe_end_point / self._time_zoom),
                                 int(self.cursor_position / self._time_zoom)))
        self.setMinimumHeight(max(parent_height, int(len(self._channels) * CHANNEL_DISPLAY_HEIGHT) + 2 * 20))
        self.repaint()

    def add_channels(self, channels: list[DataType]):
        for c in channels:
            self._channels.append(c)
        self.compute_resize()

    def zoom_out(self, factor: float = 2.0):
        self._time_zoom *= factor
        self.compute_resize()

    def zoom_in(self, factor: float = 2.0):
        self._time_zoom /= factor
        self.compute_resize()

    def move_cursor_right(self):
        self.cursor_position += self._time_zoom * 10
        self._update_7seg_text()
        self.compute_resize()

    def move_cursor_left(self):
        self.cursor_position -= self._time_zoom * 10
        if self.cursor_position < 0:
            self.cursor_position = 0.0
        self._update_7seg_text()
        self.compute_resize()

    def _update_7seg_text(self):
        txt = format_seconds(self.cursor_position).replace(':', '').replace('.', '')
        while len(txt) < 10:
            txt = "0" + txt
        txt = str(self.cue_index % 100) + txt
        while len(txt) < 12:
            txt = " " + txt
        print(txt)
        set_seven_seg_display_content(txt, update_from_gui=True)

    def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(ev)
        if ev.y() <= 20:
            self.cursor_position = ev.x() * self._time_zoom
        self.repaint()
