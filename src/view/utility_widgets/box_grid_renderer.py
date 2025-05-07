from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QPainter, QBrush, QPalette, QColor, QPixmap
from PySide6.QtWidgets import QWidget, QApplication

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent


class BoxGridItem(QObject):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        self.text: str = ""
        self._icon: QPixmap | None = None
        self.additional_render_method: callable | None = None
        self.clicked: Signal = Signal()

    def set_icon(self, icon: QPixmap | QIcon | None):
        if icon is None:
            self._icon = None
        elif isinstance(icon, QPixmap):
            self._icon = icon
        elif isinstance(icon, QIcon):
            self._icon = icon.pixmap(
                self.parent().box_width / 2 if isinstance(self.parent(), BoxGridRenderer) else 50,
                self.parent().box_height / 2 if isinstance(self.parent(), BoxGridRenderer) else 60
            )

    @property
    def pixmap(self) -> "QPixmap":
        return self._icon


class BoxGridRenderer(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._boxes: list[BoxGridItem] = []
        self._box_width = 100
        self._box_height = 120
        self._scroll_position = 0
        self._scroll_bar_size = 10
        self._border_width = 10
        self.setMinimumWidth(self._box_width + self._scroll_bar_size)
        self.setMinimumHeight(self._box_height)
        self._fg_brush = QBrush(QColor(0xdc, 0x66, 0x01))

    @property
    def box_width(self) -> int:
        return self._box_width

    @box_width.setter
    def box_width(self, new_value: int):
        self._box_width = max(new_value, 0)
        self.setMinimumWidth(self._box_width + self._scroll_bar_size)
        self.update()
        self.repaint()

    @property
    def box_height(self) -> int:
        return self._box_height

    @box_height.setter
    def box_height(self, new_value: int):
        self._box_height = max(0, new_value)
        self.setMinimumHeight(self._box_height)
        self.update()
        self.repaint()

    def add_label(self, text: str, icon: QIcon | None = None):
        b = BoxGridItem(self)
        b.text = text
        b.icon = icon
        self.add_item(b)

    def add_item(self, b: BoxGridItem):
        self._boxes.append(b)
        b.setParent(self)
        # TODO display scroll bar if boxes > height
        # TODO link scroll bar signals if scroll bar visible
        self.update()
        self.repaint()

    def paintEvent(self, event: "QPaintEvent", /):
        p = QPainter(self)
        p.device()

        width_adv_per_box = self._box_width + self._border_width
        height_adv_per_box = self._box_height + self._border_width
        boxes_per_row = int((self.width() - self._scroll_bar_size) / width_adv_per_box)

        x = event.rect().x()
        x_start = x
        x_end = x + event.rect().width()
        y = event.rect().y()
        y_end = y + event.rect().height()
        p.fillRect(event.rect(), QBrush(QApplication.palette().color(QPalette.ColorRole.Base)))
        while y <= y_end:
            x = x_start
            while x <= x_end:
                if (x + self._box_width + self._border_width) <= self.width() - self._scroll_bar_size:
                    box_index = int(int(y / height_adv_per_box) * boxes_per_row + int(x / width_adv_per_box))
                    if box_index < len(self._boxes):
                        b = self._boxes[box_index]
                        self._draw_box(p, b, x + self._border_width / 2, y + self._border_width / 2)
                x += width_adv_per_box
            y += height_adv_per_box
        # TODO render scroll bar
        p.end()

    def _draw_box(self, p: QPainter, b: BoxGridItem, x: int, y: int):
        p.setBrush(self._fg_brush)
        p.drawRect(x, y, self._box_width, self._box_height)
        s_height = p.fontMetrics().xHeight()
        p.drawText(x + 5, y + 5 + s_height, b.text)
        icon = b.pixmap
        if icon is not None:
            p.drawPixmap(x + self._box_width / 4, y + s_height + 10, icon)
        if b.additional_render_method is not None:
            b.additional_render_method(p, x, y)
