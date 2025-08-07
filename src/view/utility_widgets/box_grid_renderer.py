from collections.abc import Callable
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPalette, QPixmap, QResizeEvent, Qt
from PySide6.QtWidgets import QApplication, QWidget

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent, QPaintEvent


class BoxGridItem(QObject):
    """A box button.

     It features a text and an optional icon.
    On click, a signal 'clicked' will be emitted, which provides the data of the item.
    """

    clicked: Signal = Signal(object)

    def __init__(self, parent: QWidget | None) -> None:
        super().__init__(parent=parent)
        self._text: str = ""
        self._icon: QPixmap | None = None
        self._additional_render_method: Callable[[QPainter, int, int], None] | None = None
        self._data: object | None = None

    def set_icon(self, icon: QPixmap | QIcon | None) -> None:
        """Set the icon of this item.

        If a QIcon is passed, it will be automatically converted to the correct size.
        If a pixmap is passed, it needs to have the correct size from the beginning on.

        Args:
            icon: Icon to set.

        """
        if icon is None:
            self._icon = None
        elif isinstance(icon, QPixmap):
            self._icon = icon
        elif isinstance(icon, QIcon):
            self._icon = icon.pixmap(
                self.parent().box_width / 2 if isinstance(self.parent(), BoxGridRenderer) else 50,
                self.parent().box_height / 2 if isinstance(self.parent(), BoxGridRenderer) else 60,
            )

    @property
    def pixmap(self) -> "QPixmap | None":
        """Get the current pixmap of the item. This property might return None."""
        return self._icon

    @property
    def text(self) -> str:
        """Set or get the text of the item."""
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = str(text)

    @property
    def additional_render_method(self) -> Callable[[QPainter, int, int], None] | None:
        """Additional render method."""
        return self._additional_render_method

    @additional_render_method.setter
    def additional_render_method(self, method: Callable[[QPainter, int, int], None]) -> None:
        self._additional_render_method = method

    @property
    def data(self) -> object:
        """Store arbitrary data associated with this item."""
        return self._data

    @data.setter
    def data(self, data: object) -> None:
        self._data = data


class BoxGridRenderer(QWidget):
    """Represents a widget providing a collection of floating box buttons.

    Each box can contain text as well as icons. For special applications, custom
    rendering methods can be provided as callables.

    Example:
        ```python
        widget = BoxGridRenderer()
        for i in range(15):
            widget.add_label(f"Label {i}")
        ```

    Methods:
        item_at(index): Returns the item (Box) at the given index.

    See Also:
        BoxGridItem: For a detailed explanation of individual items.

    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._boxes: list[BoxGridItem] = []
        self._box_width = 100
        self._box_height = 120
        self._scroll_position = 0
        self._scroll_bar_size = 10
        self._border_width = 10
        self.setMinimumWidth(self._box_width + self._scroll_bar_size)
        self.setMinimumHeight(self._box_height)
        self.setMaximumHeight(65565)
        self.setMaximumWidth(65565)
        self._fg_brush = QBrush(QColor(0xDC, 0x66, 0x01))

    @property
    def box_width(self) -> int:
        """Get the width of individual items."""
        return self._box_width

    @box_width.setter
    def box_width(self, new_value: int) -> None:
        """Set the width of individual items."""
        self._box_width = max(new_value, 0)
        self.setMinimumWidth(self._box_width + self._scroll_bar_size)
        self.update()
        self.repaint()

    @property
    def box_height(self) -> int:
        """Get the height of individual items."""
        return self._box_height

    @box_height.setter
    def box_height(self, new_value: int) -> None:
        """Set the height of individual items."""
        self._box_height = max(0, new_value)
        self.setMinimumHeight(self._box_height)
        self.update()
        self.repaint()

    def add_label(self, text: str, icon: QIcon | None = None) -> None:
        """Add a new item based on the provided text.

        Args:
            text: The text of the new item.
            icon: An optional icon of the new item to add.

        """
        b = BoxGridItem(self)
        b.text = text
        b.set_icon(icon)
        self.add_item(b)

    def add_item(self, b: BoxGridItem) -> None:
        """Add an item object.

        Args:
            b : The item to add.

        """
        self._boxes.append(b)
        b.setParent(self)
        self.update()
        self.repaint()

    def _update_scroll_behavior(self) -> None:
        # TODO display scroll bar if boxes > height
        # TODO link scroll bar signals if scroll bar visible
        pass

    @override
    def resizeEvent(self, event: QResizeEvent, /) -> None:
        self._update_scroll_behavior()
        super().resizeEvent(event)

    def clear(self) -> None:
        """Clear the contained items."""
        self._boxes.clear()
        self.update()
        self.repaint()

    def item_at(self, i: int) -> BoxGridItem | None:
        """Access the desired item using the given index.

        Args:
            i (int): The index of the item to retrieve.

        Returns:
            The item at the given index, or None if it does not exist.

        """
        if not (0 <= i < len(self._boxes)):
            return None
        return self._boxes[i]

    @override
    def paintEvent(self, event: "QPaintEvent", /) -> None:
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
                        self._draw_box(p, b, int(x + self._border_width / 2), int(y + self._border_width / 2))
                x += width_adv_per_box
            y += height_adv_per_box
        # TODO render scroll bar
        p.end()

    def _draw_box(self, p: QPainter, b: BoxGridItem, x: int, y: int) -> None:
        """Draws a box. At the given location."""
        p.setBrush(self._fg_brush)
        p.drawRect(x, y, self._box_width, self._box_height)
        s_height = p.fontMetrics().xHeight()
        p.drawText(x + 5, y + 5 + s_height, b.text)
        icon = b.pixmap
        if icon is not None:
            p.drawPixmap(x + self._box_width / 4, y + s_height + 10, icon)
        if b.additional_render_method is not None:
            b.additional_render_method(p, x, y)

    @override
    def mousePressEvent(self, e: "QMouseEvent") -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            width_adv_per_box = self._box_width + self._border_width
            height_adv_per_box = self._box_height + self._border_width
            boxes_per_row = int((self.width() - self._scroll_bar_size) / width_adv_per_box)

            x = e.pos().x() - self._border_width / 2
            y = e.pos().y() - self._border_width / 2
            box_index = int(int(y / height_adv_per_box) * boxes_per_row + int(x / width_adv_per_box))
            if box_index < len(self._boxes):
                e.accept()
                box = self._boxes[box_index]
                box.clicked.emit(box.data)
