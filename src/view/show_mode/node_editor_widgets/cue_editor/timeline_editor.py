from typing import Optional

import PySide6
from PySide6.QtCore import Qt, QRectF, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QGraphicsWidget

from model import DataType
from view.show_mode.node_editor_widgets.cue_editor.cue import Cue
from view.show_mode.node_editor_widgets.cue_editor.utility import format_seconds

CHANNEL_DISPLAY_HEIGHT = 64


class TimelineContentWidget(QGraphicsWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self._last_keyframe_end_point = 0  # Defines the length of the Cue in seconds
        self._time_zoom = 0.01  # Defines how many seconds are a pixel, defaults to 1 pixel = 10ms
        self._channels = []
        self.cursor_position = 0.0
        # TODO implement

    def boundingRect(self) -> PySide6.QtCore.QRectF:
        """This method returns the required dimensions of the widget"""
        # width = 10 + self._last_keyframe_end_point / self._time_zoom
        # channel label with + a bit of extra space for a timescale below and the cursor triangle above
        # height = len(self._channels) * CHANNEL_DISPLAY_HEIGHT + 20
        dimensions = self.geometry()
        return QRectF(0, 0, dimensions.width, dimensions.height)

    def paint(self, painter: QPainter, option: PySide6.QtWidgets.QStyleOptionGraphicsItem,
              widget: Optional[PySide6.QtWidgets.QWidget] = ...) -> None:
        painter.setRenderHint(QPainter.Antialiasing)

        # Render background
        widget_dimensions = self.geometry()
        painter.fillRect(0, 0, widget_dimensions.width(), widget_dimensions.height(), QColor.fromRgb(0x3A, 0x3A, 0x3A))

        # TODO render transitions

        # render cursor
        cursor_path = QPainterPath(QPoint(int(self.cursor_position / self._time_zoom), 0))
        cursor_path.moveTo(-16, 0)
        cursor_path.lineTo(16, 0)
        cursor_path.lineTo(1, 20)
        cursor_path.lineTo(1, widget_dimensions.height() - 10)
        cursor_path.lineTo(-1, widget_dimensions.height() - 10)
        cursor_path.lineTo(-1, 20)
        cursor_path.lineTo(-16, 0)
        painter.fillPath(cursor_path, QBrush(QColor(0xFF, 0x2F, 0x2F)))

        # render timescale
        x = 0
        while x < widget_dimensions.width():
            time_str = format_seconds(x * self._time_zoom)
            painter.drawText(x, widget_dimensions.width() - 10, time_str)
            x += 10 * len(time_str)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.prepareGeometryChange()


class TimelineChannelLabel(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        # TODO implement


class TimelineContainer(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self._channel_labels_panel = QWidget()
        self._channel_labels_panel_layout = QVBoxLayout()
        self._channel_labels_panel.setLayout(self._channel_labels_panel_layout)
        layout.addWidget(self._channel_labels_panel)
        self._keyframes_panel = TimelineContentWidget()
        timeline_scroll_area = QScrollArea()
        timeline_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        timeline_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        timeline_scroll_area.setWidget(self._keyframes_panel)
        # TODO link jogwheel events to scrolling of cursor (and thus timeline_scroll_area)
        layout.addWidget(timeline_scroll_area)
        self.setLayout(layout)
        self.cue = Cue()

    def add_channel(self, channel_type: DataType):
        # TODO add TimelineChannelLabel to self._channel_labels_panel_layout
        # TODO add channel to self._keyframes_panel
        pass

    def clear_channels(self):
        """Removes all channels from the widget"""
        # TODO clear all labels from self._channel_labels_panel_layout
        # TODO reset self._keyframes_panel
        pass

    @property
    def cue(self) -> Cue:
        """Returns the edited cue."""
        return self._cue

    @cue.setter
    def cue(self, c: Cue):
        self._cue = c
        for channel in c.channel_types:
            self.add_channel(channel)

