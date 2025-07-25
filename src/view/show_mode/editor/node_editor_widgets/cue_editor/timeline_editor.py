from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QWidget

from model import DataType
from model.control_desk import BankSet, ColorDeskColumn, RawDeskColumn, set_seven_seg_display_content
from view.show_mode.editor.node_editor_widgets.cue_editor.channel_label import TimelineChannelLabel
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import (
    Cue,
    KeyFrame,
    StateColor,
    StateDouble,
    StateEightBit,
    StateSixteenBit,
)
from view.show_mode.editor.node_editor_widgets.cue_editor.timeline_content_widget import TimelineContentWidget


class TimelineContainer(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self._channel_label = TimelineChannelLabel()
        self._channel_label.sb_offset = 10
        layout.addWidget(self._channel_label)
        timeline_scroll_area = QScrollArea()
        timeline_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        timeline_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        timeline_scroll_area.verticalScrollBar().setEnabled(False)
        timeline_scroll_area.setWidgetResizable(True)
        self._keyframes_panel = TimelineContentWidget(parent)
        self._keyframes_panel.size_changed.connect(self._keyframe_panel_size_changed)
        timeline_scroll_area.setWidget(self._keyframes_panel)  # timeline_scroll_area
        # TODO link jogwheel events to scrolling of cursor (and thus timeline_scroll_area)
        layout.addWidget(timeline_scroll_area)
        self.setLayout(layout)
        self.cue = Cue()
        self._current_transition_type = "edg"

    @property
    def transition_type(self) -> str:
        return self._current_transition_type

    @transition_type.setter
    def transition_type(self, new_value: str) -> None:
        self._current_transition_type = new_value

    @property
    def bankset(self) -> BankSet:
        return self._keyframes_panel.used_bankset

    @bankset.setter
    def bankset(self, bs: BankSet) -> None:
        self._keyframes_panel.used_bankset = bs

    def add_channel(self, channel_type: DataType, name: str) -> None:
        self._channel_label.add_label(name, channel_type.format_for_filters())
        self._keyframes_panel.add_channels([channel_type])

    def remove_channel(self, c_name: str) -> None:
        i = self._channel_label.remove_label(c_name)
        if i != -1:
            self._keyframes_panel.remove_channel(i)

    def clear_channels(self) -> None:
        """Removes all channels from the widget"""
        # TODO clear all labels from self._channel_labels_panel_layout
        # TODO reset self._keyframes_panel

    @property
    def cue(self) -> Cue:
        """Returns the edited cue."""
        return self._cue

    @cue.setter
    def cue(self, c: Cue) -> None:
        self._cue = c
        # TODO clear keyframes_panel
        self._keyframes_panel.clear_cue()
        self._channel_label.clear_labels()
        for channel in c.channels:
            self.add_channel(channel[1], channel[0])
        self._keyframes_panel.cue_index = c.index_in_editor
        # TODO introduce property
        self._keyframes_panel.frames = c._frames
        self._keyframes_panel.repaint()

    def increase_zoom(self, factor: float = 2.0) -> None:
        self._keyframes_panel.zoom_in(factor)

    def decrease_zoom(self, factor: float = 2.0) -> None:
        self._keyframes_panel.zoom_out(factor)

    def move_cursor_left(self) -> None:
        self._keyframes_panel.move_cursor_left()

    def move_cursor_right(self) -> None:
        self._keyframes_panel.move_cursor_right()

    def record_pressed(self) -> None:
        p = self._keyframes_panel.cursor_position
        f = KeyFrame(self._cue)
        f.timestamp = p

        for i, chanel in enumerate(self._cue.channels):
            match chanel[1]:
                case DataType.DT_8_BIT:
                    s = StateEightBit(self._current_transition_type)
                    if self.bankset:
                        column = self.bankset.get_column_by_number(i)
                        if isinstance(column, RawDeskColumn):
                            s._value = int((column.fader_position * 256) / 65536)
                case DataType.DT_16_BIT:
                    s = StateSixteenBit(self._current_transition_type)
                    if self.bankset:
                        column = self.bankset.get_column_by_number(i)
                        if isinstance(column, RawDeskColumn):
                            s._value = column.fader_position
                case DataType.DT_DOUBLE:
                    s = StateDouble(self._current_transition_type)
                    if self.bankset:
                        column = self.bankset.get_column_by_number(i)
                        if isinstance(column, RawDeskColumn):
                            s._value = column.fader_position / 65536
                case DataType.DT_COLOR:
                    s = StateColor(self._current_transition_type)
                    if self.bankset:
                        column = self.bankset.get_column_by_number(i)
                        if isinstance(column, ColorDeskColumn):
                            s.color = column.color
                case _:
                    s = StateEightBit(self._current_transition_type)
            f.append_state(s)

        self._keyframes_panel.insert_frame(f)

    def format_zoom(self) -> str:
        return f"{int(self._keyframes_panel._time_zoom * 10000) / 10000:0>3} Sec/Pixel"

    @staticmethod
    def clear_display() -> None:
        set_seven_seg_display_content(" " * 12, True)

    def _keyframe_panel_size_changed(self, new_size: QPoint) -> None:
        if new_size.y() != self._channel_label.height():
            self._channel_label.setMinimumHeight(max(new_size.y(), self._channel_label.height()))
            self._channel_label.update()
        self.setMinimumHeight(max(self.height(), self.minimumHeight(),
                                  self._channel_label.height(), self._channel_label.minimumHeight()))
