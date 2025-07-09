from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap, QResizeEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget
from qasync import QtGui

from controller.joystick.joystick_enum import JoystickList
from model import Broadcaster
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter


class PanTiltConstantContentWidget(QLabel):
    def __init__(self, filter: PanTiltConstantFilter | None,
                 parent: QWidget = None, enable_joystick: bool = True) -> None:
        super().__init__(parent=parent)
        self.pan = 0
        self.tilt = 0
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
        self._dragged = False  # for detecting drag and drop
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.prange = 1
        self.trange = 1

        self._filter = filter

        if filter is not None:
            self._filter.register_observer(self, self.repaint)
        self.repaint()
        if enable_joystick:
            Broadcaster().handle_joystick_event.connect(self.handle_key_event)

    def repaint(self) -> None:
        canvas = QPixmap(QSize(self.width(), self.height()))
        canvas.size()
        w = canvas.width()
        h = canvas.height()
        if w == 0 or h == 0:
            return
        painter = QtGui.QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isEnabled():
            painter.fillRect(0, 0, w, h, QColor.fromRgb(0xF9, 0xF9, 0xF9))
        else:
            painter.fillRect(0, 0, w, h, QColor.fromRgb(0x80, 0x80, 0x80))
        painter.setPen(QColor.fromRgb(0xC0, 0xC0, 0xC0))
        p = 0.0
        while (p <= self.prange):
            pabs = p * w / self.prange
            painter.drawLine(pabs, 0, pabs, h)
            p += self.prange / 16
        t = 0.0
        while (t <= self.trange):
            tabs = t * h / self.trange
            painter.drawLine(0, tabs, w, tabs)
            t += self.trange / 6

        painter.setBrush(QColor.fromRgb(0x00, 0x00, 0xE0))
        pointsize = 10
        pabs = self.pan * w / self.prange
        tabs = self.tilt * h / self.trange
        painter.drawEllipse(pabs - pointsize / 2, tabs - pointsize / 2, pointsize, pointsize)

        painter.end()
        self.setPixmap(canvas)

    def mousePressEvent(self, event: QMouseEvent):
        self._dragged = True
        self.update_pan_tilt(event)
        self.repaint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragged = False
        self.repaint()

    def mouseMoveEvent(self, event: QMouseEvent):
        self.update_pan_tilt(event)
        self.repaint()

    def resizeEvent(self, event: QResizeEvent):
        self.repaint()

    def update_pan_tilt(self, event: QMouseEvent):
        if self._filter is not None:
            self._filter.pan_delta = 0.0
            self._filter.tilt_delta = 0.0
        if (self._dragged and event.x() <= self.width() and
                event.y() <= self.height() and event.x() >= 0 and event.y() >= 0):
            self.pan = event.pos().x() * self.prange / self.width()
            self.tilt = event.pos().y() * self.trange / self.height()
            if self._filter is not None:
                self._filter.pan = self.pan
                self._filter.tilt = self.tilt

    def handle_key_event(self, joystick: JoystickList, val: float, tilt: bool):
        if self._filter is None:
            return
        self._filter.set_delta(val, joystick, tilt)
