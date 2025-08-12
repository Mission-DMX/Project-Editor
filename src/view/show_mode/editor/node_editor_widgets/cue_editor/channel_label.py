"""Internal widget to provide labels for channels in timeline."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6 import QtGui
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from view.show_mode.editor.node_editor_widgets.cue_editor.view_settings import CHANNEL_DISPLAY_HEIGHT

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent


class TimelineChannelLabel(QWidget):
    """Widget providing a label for channels within a timeline.

    Use add_label in order to add a new channel label.
    """

    def __init__(self, parent: QWidget = None) -> None:
        """Initialize the channel label."""
        super().__init__(parent=parent)
        self.active_channels: dict[str, bool] = {}
        self._display_active_channel_indicator = False
        self._names: list[str] = []
        self._types: list[str] = []
        self.setMinimumWidth(2 * CHANNEL_DISPLAY_HEIGHT)
        self.setMinimumHeight(20)
        self.sb_offset = 0
        self._update()
        # TODO register with the bank set fader touch buttons to highlight a touched channel.

    def add_label(self, name: str, channel_type: str) -> None:
        """Add a new label.

        Args:
            name: The name of the channel.
            channel_type: The type of the channel. Usually 8bit, 16bit, float, or color.

        """
        self._names.append(name)
        self._types.append(channel_type)
        self.active_channels[name] = True
        self._update()

    def remove_label(self, c_name: str) -> int:
        """Remove the label with the associated channel name.

        Args:
            c_name: The name of the channel to remove.

        Returns:
            The previous index of the removed channel.

        """
        found_i = -1
        for i in range(len(self._names)):
            if self._names[i] == c_name:
                self._names.pop(i)
                self._types.pop(i)
                found_i = i
                break
        self.active_channels.pop(c_name)
        self._update()
        return found_i

    def clear_labels(self) -> None:
        """Remove all labels."""
        self._names.clear()
        self._types.clear()
        self.active_channels.clear()
        self._update()

    def _update(self) -> None:
        """Update the label properties."""
        required_height = 2 * 20 + CHANNEL_DISPLAY_HEIGHT * len(self._names) + self.sb_offset
        self.setMinimumHeight(required_height)
        self.update()

    @property
    def display_active_channel_indicator(self) -> bool:
        """Enable or disable the active channel indicator.

        Should the channels provide checkboxes indicating if they're active or not?
        """
        return self._display_active_channel_indicator

    @display_active_channel_indicator.setter
    def display_active_channel_indicator(self, value: bool) -> None:
        self._display_active_channel_indicator = value
        self.update()

    @override
    def paintEvent(self, ev: QPaintEvent) -> None:
        """Repaint the widget."""
        w = self.width()
        h = self.height()
        if w == 0 or h == 0:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, w, h, QColor.fromRgb(0x3A, 0x3A, 0x3A))

        channel_background_color = QColor.fromRgb(0x4A, 0x4A, 0x4A)
        indicator_background_color = QColor.fromRgb(0x22, 0x22, 0x22)
        indicator_active_color = QColor.fromRgb(0xFF, 0x4A, 0x4A)
        for i, channel_name in enumerate(self._names):
            if (i % 2) == 0:
                painter.fillRect(
                    0, 20 + i * CHANNEL_DISPLAY_HEIGHT, w, CHANNEL_DISPLAY_HEIGHT, channel_background_color
                )
            painter.drawText(17, 45 + i * CHANNEL_DISPLAY_HEIGHT, channel_name)
            if len(self._types) > i:
                painter.drawText(25, 60 + i * CHANNEL_DISPLAY_HEIGHT, self._types[i])
            if self._display_active_channel_indicator:
                painter.fillRect(5, 50 + i * CHANNEL_DISPLAY_HEIGHT, 15, 15, indicator_background_color)
                if channel_name in self.active_channels:
                    painter.fillRect(6, 51 + i * CHANNEL_DISPLAY_HEIGHT, 13, 13, indicator_active_color)
        painter.end()

    def mousePressEvent(self, ev: QMouseEvent) -> None:  # NOQA: N802 This overrides a Qt6 native method
        """Handle user mouse input."""
        super().mousePressEvent(ev)
        if not self._display_active_channel_indicator:
            return
        if 5 <= ev.x() <= 20:
            y = ev.y()
            for i, channel_name in enumerate(self._names):
                if 50 + i * CHANNEL_DISPLAY_HEIGHT <= y <= 65 + i * CHANNEL_DISPLAY_HEIGHT:
                    self.active_channels[channel_name] = not self.active_channels[channel_name]
                    break
        self.update()
