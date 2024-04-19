from PySide6 import QtGui, QtCore
from PySide6.QtCore import QRect, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QTransform, QPaintEvent, QFontMetrics, QMouseEvent
from PySide6.QtWidgets import QWidget, QSizePolicy

from controller.ofl.fixture import UsedFixture
from model.virtual_filters.effects_stacks.vfilter import EffectsStack
from model.virtual_filters.effects_stacks.ChaningEffectDummy import ChainingEffectDummy
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from model.virtual_filters.effects_stacks.effect_socket import EffectsSocket


class EffectCompilationWidget(QWidget):

    effect_added = Signal()
    active_config_widget_changed = Signal(QWidget)

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
        self._slot_counter: list[tuple[str, Effect]] = []
        self._added_fixtures: set[UsedFixture] = set()
        self._painting_active = False
        self._config_button_positions: list[tuple[int, int, QWidget]] = []
        self._active_config_widget: QWidget | None = None
        self.repaint()

    def add_fixture_or_group(self, fg: UsedFixture):
        if fg in self._added_fixtures:
            return
        self._added_fixtures.add(fg)
        es = EffectsSocket(fg)
        self._filter.sockets.append(es)
        self.setMinimumHeight(len(self._filter.sockets) * 50)  # FIXME why do we not get our desired height?
        self.repaint()

    def paintEvent(self, redraw_hint: QPaintEvent):
        if self._painting_active:
            return
        self._painting_active = True
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
        self._slot_counter.clear()
        self._config_button_positions.clear()

        if len(self._filter.sockets) > 0:
            y = 15
            for s in self._filter.sockets:
                y = self._paint_socket_stack(s, p, w, h, y, area_to_update)
            if y > self.minimumHeight():
                self.setMinimumHeight(y + 15)
        else:
            p.setBrush(QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC)))
            no_socket_hint_str = "There are no sockets defined. Please add some from the available fixtures."
            fm: QFontMetrics = p.fontMetrics()
            text_width = fm.horizontalAdvance(no_socket_hint_str)
            text_height = fm.height()
            p.drawText(int(w / 2 - text_width / 2), int(h / 2 - text_height / 2), no_socket_hint_str)

        p.end()
        self._painting_active = False

    def render_slot(self, x: int, y: int, first: bool, effect: Effect, p: QPainter) -> tuple[int, int]:
        slot_type: EffectType = effect.get_output_slot_type()
        fm = self.fontMetrics()
        light_blue_brush = QBrush(QColor.fromRgb(0x03, 0x9B, 0xE5))
        light_gray_color = QBrush(QColor.fromRgb(0xaa, 0xaa, 0xaa))
        p.setBrush(light_gray_color)
        old_transform = p.transform()
        transform_90deg = QTransform()
        transform_90deg.rotate(-90.0)
        socket_height = 35

        if first:
            # draw slot type name
            p.setTransform(transform_90deg, True)
            type_name = slot_type.human_readable_name
            text_length = fm.horizontalAdvance(type_name)
            socket_height = max(socket_height, text_length)
            p.drawText(-y - text_length, x - 25, type_name)
            p.setTransform(old_transform, False)
            x = x - 50

        # draw Effect name
        effect_name = effect.get_human_filter_name()
        text_length = fm.horizontalAdvance(effect_name)
        x -= text_length + 10
        p.drawText(x, y + 10, effect_name)
        socket_height = max(socket_height, fm.height() + 10)

        # draw effect config button
        config_widget = effect.get_configuration_widget()
        if config_widget is not None:
            y += 25
            p.setBrush(QBrush(QColor.fromRgb(0x30, 0x30, 0x30) if config_widget != self._active_config_widget else
                              QColor.fromRgb(0, 0xff, 0xff)))
            p.drawRoundedRect(x, y, 20, 20, 3.0, 3.0)
            p.setBrush(light_gray_color)
            p.drawLine(x + 5, y + 10, x + 15, y + 10)
            p.drawLine(x + 10, y + 5, x + 10, y + 15)
            self._config_button_positions.append((x, y, config_widget))
            y += 5
        x -= 10

        # recursively render all effects attached to slots
        text_height = fm.height()
        for slot_name, e in effect.slot_definitions():
            rendered_slots: set[str] = set()

            human_slot_name = effect.get_human_slot_name(slot_name)
            text_length = fm.horizontalAdvance(human_slot_name)
            y += text_length
            p.drawText(x, y, human_slot_name)
            # draw slot indicator symbol
            p.drawLine(x - 7, y - 2, x - 7, y - 7)
            p.drawLine(x - 2, y - 2, x - 2, y - 7)
            p.drawLine(x - 7, y - 7, x - 2, y - 2)
            p.drawLine(x - 7, y - 2, x - 2, y - 7)
            y += 10

            if e is not None:
                # draw attached slot
                old_y = y
                old_x = x
                x -= 10
                x, y = self.render_slot(x, y, False, e, p)
                p.drawLine(old_x - 3, old_y - 3, old_x - 3, y)
            else:
                # render insertion hint for empty slots
                if self._pending_effect:
                    can_attach_effect = False
                    supported_slot_types = effect.get_accepted_input_types()[slot_name]
                    for supported_target in supported_slot_types:
                        can_attach_effect |= Effect.can_convert_slot(self._pending_effect.get_output_slot_type(),
                                                                     supported_target)
                    if can_attach_effect:
                        if slot_name not in rendered_slots:
                            # render placement hint
                            slot_counter_str = str(len(self._slot_counter))
                            x -= 10
                            slot_counter_str_width = fm.horizontalAdvance(slot_counter_str)
                            p.fillRect(x - slot_counter_str_width - 6, int(y + socket_height / 2 - text_height / 2 - 3),
                                       slot_counter_str_width + 6, text_height / 2 + 6, light_blue_brush)
                            p.drawText(x - slot_counter_str_width - 3, y + socket_height / 2 + 3, slot_counter_str)
                            rendered_slots.add(slot_name)
                            dummy_effect = ChainingEffectDummy(effect, slot_name, supported_slot_types)
                            self._slot_counter.append((slot_name, dummy_effect))

        y += socket_height
        return x, y

    def _paint_socket_stack(self, s: EffectsSocket, p: QPainter, w: int, h: int, y: int, drawing_area: QRect) -> int:
        light_gray_brush = QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC))
        p.setBrush(light_gray_brush)
        initial_y = y
        old_transform = p.transform()
        transform_90deg = QTransform()
        transform_90deg.rotate(-90.0)
        fm = p.fontMetrics()
        p.drawLine(0, y, w, y)
        y += 15

        if s.has_color_property:
            x, y = self.render_slot(self.width(), y, True, s.get_socket_or_dummy(EffectType.COLOR), p)

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
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)

    def add_effect_to_slot(self, i: int) -> bool:
        if self._pending_effect is None or i >= len(self._slot_counter):
            return False
        slot_id, candidate_effect = self._slot_counter[i]
        if not candidate_effect.attach(slot_id, self._pending_effect):
            return False
        self._pending_effect = None
        self._slot_counter = []
        self.effect_added.emit()
        self.update()
        return True

    def get_maximum_slot_counter(self) -> int:
        return len(self._slot_counter) - 1

    def mousePressEvent(self, event: QMouseEvent):
        for x, y, widget in self._config_button_positions:
            if x < event.x() < x + 25:
                if y < event.y() < y + 25:
                    self._active_config_widget = widget
                    self.active_config_widget_changed.emit(widget)
                    self.update()
                    return
