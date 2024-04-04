from PySide6 import QtGui
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QTransform, QPaintEvent, QFontMetrics
from PySide6.QtWidgets import QWidget, QSizePolicy

from controller.ofl.fixture import UsedFixture
from model.virtual_filters import EffectsStack
from model.virtual_filters.effects_stacks.color_effects import ColorEffect
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from model.virtual_filters.effects_stacks.effect_socket import EffectsSocket


class EffectCompilationWidget(QWidget):

    effect_added = Signal()

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
        self._pending_effect: Effect | None = None
        self._slot_counter: int = 0
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
        self._slot_counter = 0

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
        light_blue_brush = QBrush(QColor.fromRgb(0x03, 0x9B, 0xE5))
        p.setBrush(light_gray_brush)
        initial_y = y
        old_transform = p.transform()
        transform_90deg = QTransform()
        transform_90deg.rotate(-90.0)
        fm = p.fontMetrics()
        p.drawLine(0, y, w, y)
        y += 5
        # TODO write method that renders slots in a generic way
        if s.has_color_property:
            p.setTransform(transform_90deg, True)
            text_length = fm.horizontalAdvance("Color")
            socket_height = max(35, text_length)
            p.drawText(-y - text_length, w - 25, "Color")
            p.setTransform(old_transform, False)
            x = w - 50
            text_height = fm.height()
            for e in s.color_socket:
                p.drawLine(x, y + 1, x, y + socket_height - 2)
                name = e.get_human_filter_name()
                name_length = fm.horizontalAdvance(name) + 10
                p.drawText(x - name_length, y + text_height + 10, name)
                x -= (name_length + 10)
                # TODO draw effect config button
                # TODO update socket height if there are further branching inputs to effects
                # TODO check if the effect on top of this socket can accept the parameters.
            if self._pending_effect is not None:
                if Effect.can_convert_slot(self._pending_effect.get_slot_type(), EffectType.COLOR):
                    slot_counter_str = str(self._slot_counter)
                    x -= 10
                    slot_counter_str_width = fm.horizontalAdvance(slot_counter_str)
                    p.fillRect(x - slot_counter_str_width - 6, int(y + socket_height / 2 - text_height / 2 - 3),
                               slot_counter_str_width + 6, text_height / 2 + 6, light_blue_brush)
                    p.drawText(x - slot_counter_str_width - 3, y + socket_height / 2 + 3, slot_counter_str)
                    self._slot_counter += 1
            y += socket_height
        socket_name = s.target.name
        socket_name_width = fm.horizontalAdvance(socket_name)
        p.setTransform(transform_90deg, True)
        y = max(y, socket_name_width + initial_y)
        p.drawText(-int(initial_y - (initial_y - y) / 2 + socket_name_width / 2), w - 10, socket_name)
        p.setTransform(old_transform, False)
        y += 5
        return y

    def load_effect_to_add(self, e: Effect | None):
        self._pending_effect = e
        # TODO change jogwheel input to select slot for add operation
        self.update()

    def add_effect_to_slot(self, i: int):
        if self._pending_effect is None:
            return False
        slots = 0
        candidate = self._pending_effect.get_slot_type()
        for socket in self._filter.sockets:
            slot_valid = False
            if socket.has_color_property and Effect.can_convert_slot(candidate, EffectType.COLOR):
                slot_valid = True
            # TODO implement for other slot types
            # TODO implement for branching slots
            # TODO check if the effect on top of this socket can accept the parameters.
            if slot_valid:
                if slots == i:
                    if not isinstance(self._pending_effect, ColorEffect):
                        return False  # TODO instantiate adapter
                    socket.color_socket.append(self._pending_effect)
                    self._pending_effect = None
                    self.effect_added.emit()
                    self.update()
                    return True
                else:
                    slots += 1
        return False

    def get_maximum_slot_counter(self) -> int:
        if self._pending_effect is None:
            return 0
        slots = 0
        candidate = self._pending_effect.get_slot_type()
        for socket in self._filter.sockets:
            if socket.has_color_property and Effect.can_convert_slot(candidate, EffectType.COLOR):
                slots += 1
            # TODO implement for other slot types
            # TODO implement for branching slots
            # TODO check if the effect on top of this socket can accept the parameters.
        return slots
