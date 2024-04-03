from PySide6 import QtGui
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QTransform, QPaintEvent, QFontMetrics
from PySide6.QtWidgets import QWidget, QSizePolicy

from controller.ofl.fixture import UsedFixture
from model.virtual_filters import EffectsStack
from model.virtual_filters.effects_stacks.effect_socket import EffectsSocket


class EffectCompilationWidget(QWidget):

    _background_css = """
    background-image: repeating-linear-gradient(
        90deg,
        #505050,
        #151515 1px
    ), repeating-linear-gradient(
      0deg,
      #303030,
      #101010 1px
    );
    background-blend-mode: screen;
    """

    def __init__(self, filter: EffectsStack, parent: QWidget):
        super().__init__(parent=parent)
        self._filter = filter
        self.setMinimumWidth(600)
        self.setSizePolicy(
            QSizePolicy.MinimumExpanding,
            QSizePolicy.MinimumExpanding
        )
        # self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # self.setStyleSheet("background-color: gray;")
        self.repaint()

    def add_fixture_or_group(self, fg: UsedFixture):
        es = EffectsSocket(fg)
        self._filter.sockets.append(es)
        self.setMinimumHeight(len(self._filter.sockets) * 50)  # FIXME why do we not get our desired height?
        self.repaint()

    def paintEvent(self, redraw_hint: QPaintEvent):
        h = self.height()
        w = self.width()
        if w == 0 or h == 0:
            return
        p = QtGui.QPainter(self)
        p.setFont(self.font())
        area_to_update = redraw_hint.rect()
        p.setRenderHint(QPainter.Antialiasing)
        color_dark_gray = QColor.fromRgb(0x3A, 0x3A, 0x3A)
        p.fillRect(0, 0, w, h, color_dark_gray)

        if len(self._filter.sockets) > 0:
            y = 0
            for s in self._filter.sockets:
                y = self._paint_socket_stack(s, p, w, h, y, area_to_update)
        else:
            p.setBrush(QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC)))
            no_socket_hint_str = "There are no sockets defined. Please add some from the available fixtures."
            fm: QFontMetrics = p.fontMetrics()
            text_width = fm.horizontalAdvance(no_socket_hint_str)
            text_height = fm.height()
            p.drawText(int(w / 2 - text_width / 2), int(h / 2 - text_height / 2), no_socket_hint_str)

        p.end()

    def _paint_socket_stack(self, s: EffectsSocket, p: QPainter, w: int, h: int, y: int, drawing_area: QRect) -> int:
        light_gray_brush = QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC))
        p.setBrush(light_gray_brush)
        y += 5
        p.drawLine(0, y, w, y)
        y += 5
        if s.has_color_property:
            transform = QTransform()
            old_transform = p.transform()
            transform.rotate(90.0)
            p.setTransform(transform, True)
            p.drawText(y, 15, "Color")
            p.setTransform(old_transform)
            y += 35
        return y
