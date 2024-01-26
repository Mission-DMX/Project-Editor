import pyjoystick
from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QPainter, QColor, QPixmap, QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QLabel, QWidget, QSizePolicy
from pyjoystick.sdl2 import run_event_loop, Key
from qasync import QtGui

from model import Scene, BoardConfiguration
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter


class PanTiltConstantContentWidget(QLabel):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
        self._dragged = False   #  for detecting drag and drop
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.prange = 720
        self.trange = 270

        # just for now:
        scene = Scene(10, "tst", BoardConfiguration())
        self._filter = PanTiltConstantFilter(scene, filter_id = "this new filter", filter_type = -2)

        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update_time_passed)
        self._timer.start()

        self.joy_input_x = 0.0
        self.joy_input_y = 0.0
        mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                             handle_key_event=self.handle_key_event)
        mngr.start()

        self.repaint()

    def repaint(self) -> None:
        canvas = QPixmap(QSize(self.width(), self.height()))
        canvas.size()
        w = canvas.width()
        h = canvas.height()
        if w == 0 or h == 0:
            return
        painter = QtGui.QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, w, h, QColor.fromRgb(0xF9, 0xF9, 0xF9))
        painter.setPen(QColor.fromRgb(0xE0, 0xE0, 0xE0))
        for p in range(0, self.prange+1, 45):
            pabs = p * w / self.prange
            painter.drawLine(pabs, 0, pabs, h)
        for t in range(0, self.trange+1, 45):
            tabs = t * h / self.trange
            painter.drawLine(0, tabs, w, tabs)

        painter.setBrush(QColor.fromRgb(0x00, 0x00, 0xE0))
        pointsize = 10
        pabs = self._filter.pan * w / self.prange
        tabs = self._filter.tilt * h / self.trange
        painter.drawEllipse(pabs-pointsize/2, tabs-pointsize/2, pointsize, pointsize)

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

    def resizeEvent(self, event):
        self.repaint()

    def update_pan_tilt(self, event: QMouseEvent):
        self.joy_input_x = 0.0
        self.joy_input_y = 0.0
        if self._dragged and event.x() <= self.width() and event.y() <= self.height() and event.x() >= 0 and event.y() >= 0:
            self._filter.pan = event.pos().x() * self.prange / self.width()
            self._filter.tilt = event.pos().y() * self.trange / self.height()

    def handle_key_event(self, key):
        # print(key, '-', key.keytype, '-', key.number, '-', key.value)
        if key.keytype == Key.AXIS:
            if key.number == 0:
                self.joy_input_x = key.value
            elif key.number == 1:
                self.joy_input_y = key.value

    def update_time_passed(self):
        self._filter.pan = min(max(self._filter.pan + 5 * self.joy_input_x, 0.0), self.prange)
        self._filter.tilt = min(max(self._filter.tilt + 5 * self.joy_input_y, 0.0), self.trange)
        self.repaint()
