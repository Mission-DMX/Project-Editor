from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QScrollArea

from model import DataType
from model.control_desk import set_seven_seg_display_content
from view.show_mode.node_editor_widgets.cue_editor.channel_label import TimelineChannelLabel
from view.show_mode.node_editor_widgets.cue_editor.cue import Cue
from view.show_mode.node_editor_widgets.cue_editor.timeline_content_widget import TimelineContentWidget


class TimelineContainer(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self._channel_label = TimelineChannelLabel()
        layout.addWidget(self._channel_label)
        timeline_scroll_area = QScrollArea()
        timeline_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        timeline_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._keyframes_panel = TimelineContentWidget(parent)
        timeline_scroll_area.setWidget(self._keyframes_panel)  # timeline_scroll_area
        # TODO link jogwheel events to scrolling of cursor (and thus timeline_scroll_area)
        layout.addWidget(timeline_scroll_area)
        self.setLayout(layout)
        self.cue = Cue()

    def add_channel(self, channel_type: DataType, name: str):
        self._channel_label.add_label(name, channel_type.format_for_filters())
        self._keyframes_panel.add_channels([channel_type])
        print("Added channel '{}' of type {}.".format(name, channel_type.format_for_filters()))
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
        i = 0
        # TODO clear keyframes_panel
        for channel in c.channel_types:
            i += 1
            self.add_channel(channel, str(i))
        # TODO introduce property
        self._keyframes_panel.frames = c._frames
        self._keyframes_panel.repaint()

    def increase_zoom(self, factor: float = 2.0):
        self._keyframes_panel.zoom_in(factor)

    def decrease_zoom(self, factor: float = 2.0):
        self._keyframes_panel.zoom_out(factor)

    def move_cursor_left(self):
        self._keyframes_panel.move_cursor_left()

    def move_cursor_right(self):
        self._keyframes_panel.move_cursor_right()

    def record_pressed(self):
        # TODO implement
        pass

    def format_zoom(self) -> str:
        return "{0:0>3} Sec/Pixel".format(int(self._keyframes_panel._time_zoom * 10000) / 10000)
    
    @staticmethod
    def clear_display():
        set_seven_seg_display_content(" " * 12, True)

