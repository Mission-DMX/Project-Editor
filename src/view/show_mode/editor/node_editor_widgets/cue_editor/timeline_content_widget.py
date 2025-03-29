# coding=utf-8
import PySide6
from PySide6 import QtGui
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPaintEvent
from PySide6.QtWidgets import QWidget

from model import DataType
from model.control_desk import BankSet, ColorDeskColumn, RawDeskColumn, set_seven_seg_display_content
from view.show_mode.editor.node_editor_widgets.cue_editor.keyframe_state_edit_dialog import KeyFrameStateEditDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import (KeyFrame, State, StateColor, StateDouble,
                                                                            StateEightBit, StateSixteenBit)
from view.show_mode.editor.node_editor_widgets.cue_editor.utility import format_seconds
from view.show_mode.editor.node_editor_widgets.cue_editor.view_settings import CHANNEL_DISPLAY_HEIGHT


class TimelineContentWidget(QWidget):
    size_changed = Signal(QPoint)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self._last_keyframe_end_point = 0  # Defines the length of the Cue in seconds
        self._time_zoom = 0.01  # Defines how many seconds are a pixel, defaults to 1 pixel = 10ms
        self._channels = []
        self.frames: list[KeyFrame] = []
        self.cursor_position = 3.0
        self._drag_begin: tuple[int, int] = None
        self.compute_resize()
        self._cue_index: int = 0
        self.used_bankset: BankSet = None
        self._last_clicked_kf_state: State = None

    @property
    def cue_index(self) -> int:
        return self._cue_index

    @cue_index.setter
    def cue_index(self, arg: int):
        if arg > 0:
            self._cue_index = arg
            self._update_7seg_text()

    def paintEvent(self, ev: QPaintEvent) -> None:
        # TODO we should implement to only redraw required areas based on the hints provided within ev
        w = self.width()
        h = self.height()
        if w == 0 or h == 0:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Render background
        painter.fillRect(0, 0, w, h, QColor.fromRgb(0x3A, 0x3A, 0x3A))

        # render transitions
        i = 0
        channel_background_color = QColor.fromRgb(0x4A, 0x4A, 0x4A)
        for _ in self._channels:
            if (i % 2) == 0:
                painter.fillRect(0, 20 + i * CHANNEL_DISPLAY_HEIGHT, w, CHANNEL_DISPLAY_HEIGHT,
                                 channel_background_color)
            i += 1

        if self.isEnabled():
            marker_color = QColor.fromRgb(0xFF, 0xFF, 0x00)
        else:
            marker_color = QColor.fromRgb(0x80, 0x80, 0x00)
        marker_brush = QBrush(marker_color)
        light_gray_brush = QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC))
        kf_line_brush = QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC))
        kf_line_brush.setStyle(Qt.HorPattern)
        for kf in self.frames:
            if kf:
                i = 0
                x = int(kf.timestamp / self._time_zoom)
                painter.setBrush(kf_line_brush)
                kf_states = kf._states
                painter.drawLine(x, 20, x, len(kf_states) * CHANNEL_DISPLAY_HEIGHT + 20)
                painter.setBrush(light_gray_brush)
                for s in kf_states:
                    y = 40 + i * CHANNEL_DISPLAY_HEIGHT
                    if s == self._last_clicked_kf_state:
                        marker_path = QPainterPath(QPoint(x, y - 2))
                        marker_path.lineTo(x + 12, y + 10)
                        marker_path.lineTo(x, y + 22)
                        marker_path.lineTo(x - 12, y + 10)
                        marker_path.lineTo(x, y - 2)
                        painter.fillPath(marker_path, QBrush(QColor.fromRgb(0, 50, 255)))
                    marker_path = QPainterPath(QPoint(x, y))
                    marker_path.lineTo(x + 10, y + 10)
                    marker_path.lineTo(x, y + 20)
                    marker_path.lineTo(x - 10, y + 10)
                    marker_path.lineTo(x, y)
                    if isinstance(s, StateColor):
                        r, g, b = s.color.to_rgb()
                        selected_brush = QBrush(QColor.fromRgb(r, g, b))
                        painter.drawText(x + 15, y + 21, str(int(s.color.intensity * 100)) + "%")
                    elif isinstance(s, StateDouble):
                        selected_brush = marker_brush
                        painter.drawText(x + 15, y + 21, f"{s._value:10.4f}")
                    else:
                        selected_brush = marker_brush
                        painter.drawText(x + 15, y + 21, str(s._value))
                    painter.fillPath(marker_path, selected_brush)
                    painter.drawText(x + 15, y + 9, s.transition)
                    i += 1

        # render cursor, timescale and bars
        painter.setBrush(light_gray_brush)
        painter.drawLine(0, 20, w, 20)
        painter.drawLine(0, h - 20, w, h - 20)
        # render timescale
        for y in [20, h]:
            x = 0
            painter.setBrush(light_gray_brush)
            while x < w:
                painter.drawLine(x, y - 20, x, y)
                time_str = format_seconds(x * self._time_zoom)
                painter.drawText(x, y - 2, time_str)
                x += 10 * len(time_str)
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

        painter.end()

    def mousePressEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        super().mousePressEvent(ev)
        self._drag_begin = (ev.x(), ev.y())
        self.update()

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.size_changed.emit(QPoint(self.width(), self.height()))

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

    def remove_channel(self, i):
        self._channels.pop(i)
        self.compute_resize()

    def insert_frame(self, f: KeyFrame):
        self.frames.append(f)
        self._last_clicked_kf_state = None
        self.repaint()

    def zoom_out(self, factor: float = 2.0):
        if not self.isEnabled():
            return
        self._last_clicked_kf_state = None
        self._time_zoom *= factor
        self.compute_resize()

    def zoom_in(self, factor: float = 2.0):
        if not self.isEnabled():
            return
        self._last_clicked_kf_state = None
        self._time_zoom /= factor
        self.compute_resize()

    def move_cursor_right(self):
        if not self.isEnabled():
            return
        self.cursor_position += self._time_zoom * 10
        self._last_clicked_kf_state = None
        self._update_7seg_text()
        self.compute_resize()

    def move_cursor_left(self):
        if not self.isEnabled():
            return
        self.cursor_position -= self._time_zoom * 10
        if self.cursor_position < 0:
            self.cursor_position = 0.0
        self._last_clicked_kf_state = None
        self._update_7seg_text()
        self.compute_resize()

    def _update_7seg_text(self):
        txt = format_seconds(self.cursor_position).replace(':', '').replace('.', '')
        while len(txt) < 10:
            txt = "0" + txt
        txt = str(self._cue_index % 100) + txt
        while len(txt) < 12:
            txt = " " + txt
        set_seven_seg_display_content(txt, update_from_gui=True)

    def mouseReleaseEvent(self, ev: PySide6.QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(ev)
        if not self.isEnabled():
            return
        if ev.y() <= 20:
            clicked_timeslot = ev.x() * self._time_zoom
            self.cursor_position = clicked_timeslot
            self._update_7seg_text()
        else:
            if 20 <= ((ev.y() - 20) % CHANNEL_DISPLAY_HEIGHT) <= 40:
                state_width = 10
            else:
                state_width = 1
            clicked_timeslot_lower = (ev.x() - state_width) * self._time_zoom
            clicked_timeslot_upper = (ev.x() + state_width) * self._time_zoom
            for kf in self.frames:
                if clicked_timeslot_lower <= kf.timestamp <= clicked_timeslot_upper:
                    self._clicked_on_keyframe(kf, ev.y())
                    break
        self.repaint()

    def _clicked_on_keyframe(self, kf: KeyFrame, y: int):
        state_index = int((y - 20) / CHANNEL_DISPLAY_HEIGHT)
        states = kf._states
        double_click_issued = False
        if state_index < len(states):
            new_state = states[state_index]
            if new_state == self._last_clicked_kf_state:
                double_click_issued = True
            self._last_clicked_kf_state = new_state
        else:
            self._last_clicked_kf_state = None
            new_state = None
        if self.used_bankset:
            kf_states = states
            i = 0
            for b in self.used_bankset.banks:
                for c in b.columns:
                    if i < len(kf_states):
                        s = kf_states[i]
                        if isinstance(c, ColorDeskColumn) and isinstance(s, StateColor):
                            c.color = s.color
                        elif isinstance(c, RawDeskColumn):
                            if isinstance(s, StateEightBit):
                                c.fader_position = int((s._value / 256) * 65536)
                            elif isinstance(s, StateSixteenBit):
                                c.fader_position = int(s._value)
                            elif isinstance(s, StateDouble):
                                c.fader_position = int(s._value * 65536)
                        i += 1
                    else:
                        break
            self.used_bankset.push_messages_now()
        if double_click_issued:
            self._dialog = KeyFrameStateEditDialog(self.parent(), kf, new_state,
                                                   self.compute_resize)
            self._dialog.open()

    def clear_cue(self):
        self._channels.clear()
        self.cursor_position = 0.0
        self.frames = []
        self._last_keyframe_end_point = 0
        self._update_7seg_text()
        self.compute_resize()
