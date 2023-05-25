from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QScrollArea, QHBoxLayout, QTableWidget, \
    QTableWidgetItem, QFormLayout, QComboBox, QCheckBox, QPushButton, QLabel

from model import DataType
from model.broadcaster import Broadcaster
from view.show_mode.node_editor_widgets.cue_editor.cue import Cue, EndAction
from view.show_mode.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.node_editor_widgets.node_editor_widget import NodeEditorFilterConfigWidget


class CueEditor(NodeEditorFilterConfigWidget):

    def _get_configuration(self) -> dict[str, str]:
        # TODO implement
        return dict()

    def _load_configuration(self, conf: dict[str, str]):
        # TODO implement
        pass

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        # TODO implement
        pass

    def _get_parameters(self) -> dict[str, str]:
        # TODO improve channel naming by introducing channel name list
        from ctypes import c_int64
        i = c_int64(0)

        def increment(num: c_int64) -> int:
            num.value += 1
            return num.value
        d = {
                "end_handling": "start_again" if self._global_restart_on_end else "hold",
                "mapping": ";".join(["channel_{}:{}".format(increment(i), t.format_for_filters()) for t in self._cues[0].channel_types ]) if len(self._cues) > 0 else "",
                "cuelist": "$".join([c.format_cue() for c in self._cues])
            }
        return d

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self._parent_widget = QWidget(parent=parent)
        top_layout = QVBoxLayout()

        # configure top widgets
        cue_list_and_current_settings_container = QWidget(self._parent_widget)
        cue_list_and_current_settings_container_layout = QHBoxLayout()
        self._cue_list_widget = QTableWidget(cue_list_and_current_settings_container)
        self._cue_list_widget.setColumnCount(3)
        self._cue_list_widget.setHorizontalHeaderLabels(["Cue Number", "Duration", "End Action"])
        cue_list_and_current_settings_container_layout.addWidget(self._cue_list_widget)
        cue_settings_container = QWidget(parent=self._parent_widget)
        cue_settings_container_layout = QFormLayout()
        self._current_cue_end_action_select_widget = QComboBox(cue_settings_container)
        self._current_cue_end_action_select_widget.addItems(EndAction.formatted_value_list())
        cue_settings_container_layout.addRow("End Action", self._current_cue_end_action_select_widget)
        self._current_cue_another_play_pressed_checkbox = QCheckBox("Restart cue on Play pressed", self._parent_widget)
        cue_settings_container_layout.addRow("", self._current_cue_another_play_pressed_checkbox)

        self._zoom_label: QLabel = None
        self.setup_zoom_panel(cue_settings_container, cue_settings_container_layout)
        cue_settings_container.setLayout(cue_settings_container_layout)
        cue_list_and_current_settings_container_layout.addWidget(cue_settings_container)
        cue_list_and_current_settings_container.setLayout(cue_list_and_current_settings_container_layout)
        top_layout.addWidget(cue_list_and_current_settings_container)

        self.configure_toolbar(top_layout)

        v_scroll_area = QScrollArea()
        v_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        v_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # TODO link up/down button events to scrolling of v_scroll_area
        self._timeline_container = TimelineContainer(v_scroll_area)
        v_scroll_area.setWidget(self._timeline_container)
        top_layout.addWidget(v_scroll_area)
        self._parent_widget.setLayout(top_layout)
        self._jw_zoom_mode = False
        Broadcaster.desk_media_rec_pressed.connect(self.rec_pressed)
        Broadcaster.jogwheel_rotated_right.connect(self.jg_right)
        Broadcaster.jogwheel_rotated_left.connect(self.jg_left)
        Broadcaster.desk_media_scrub_pressed.connect(self.scrub_pressed)
        Broadcaster.desk_media_scrub_released.connect(self.scrub_released)

        self._set_zoom_label_text()
        self._global_restart_on_end: bool = False
        self._cues: list[Cue] = []
        self.add_cue(Cue())  # FIXME

    def setup_zoom_panel(self, cue_settings_container, cue_settings_container_layout):
        zoom_panel = QWidget(cue_settings_container)
        zoom_panel_layout = QHBoxLayout()
        zoom_panel.setLayout(zoom_panel_layout)
        self._zoom_label = QLabel(zoom_panel)
        zoom_panel_layout.addWidget(self._zoom_label)
        increase_zoom_button = QPushButton("+", zoom_panel)
        increase_zoom_button.pressed.connect(self.increase_zoom)
        zoom_panel_layout.addWidget(increase_zoom_button)
        decrease_zoom_button = QPushButton("-", zoom_panel)
        decrease_zoom_button.pressed.connect(self.decrease_zoom)
        zoom_panel_layout.addWidget(decrease_zoom_button)
        cue_settings_container_layout.addRow("Zoom", zoom_panel)

    def configure_toolbar(self, top_layout):
        toolbar = QToolBar(parent=self._parent_widget)
        toolbar_add_cue_action = QAction("Add Cue", self._parent_widget)
        toolbar_add_cue_action.setStatusTip("Add a new cue to the stack")
        toolbar_add_cue_action.triggered.connect(self._add_button_clicked)
        toolbar.addAction(toolbar_add_cue_action)
        toolbar_add_channel_action = QAction("Add Channel", self._parent_widget)
        toolbar_add_channel_action.setStatusTip("Add a new channel to the filter")
        toolbar_add_channel_action.triggered.connect(self._add_channel_button_pressed)
        toolbar.addAction(toolbar_add_channel_action)
        toolbar_remove_channel_action = QAction("Remove Channel", self._parent_widget)
        toolbar_remove_channel_action.setStatusTip("Removes a channel from the filter")
        toolbar_remove_channel_action.setEnabled(False)
        toolbar_remove_channel_action.triggered.connect(self._remove_channel_button_pressed)
        toolbar.addAction(toolbar_remove_channel_action)
        top_layout.addWidget(toolbar)

    def _set_zoom_label_text(self):
        self._zoom_label.setText(self._timeline_container.format_zoom())

    def add_cue(self, cue: Cue) -> int:
        target_row = self._cue_list_widget.rowCount() + 1
        self._cue_list_widget.setRowCount(target_row)
        self._cue_list_widget.setItem(target_row, 0, QTableWidgetItem(str(target_row)))
        self._cue_list_widget.setItem(target_row, 1, QTableWidgetItem(cue.duration_formatted))
        self._cue_list_widget.setItem(target_row, 2, QTableWidgetItem(str(cue)))
        return target_row

    def select_cue(self, cue_index: int):
        if cue_index < 0 or cue_index >= len(self._cues):
            return
        c = self._cues[cue_index]
        self._timeline_container.cue = c
        self._current_cue_end_action_select_widget.setCurrentIndex(c.end_action.value)
        self._current_cue_another_play_pressed_checkbox.setChecked(c.restart_on_another_play_press)
        self._cue_list_widget.selectRow(cue_index)

    def increase_zoom(self):
        self._timeline_container.increase_zoom()
        self._set_zoom_label_text()

    def decrease_zoom(self):
        self._timeline_container.decrease_zoom()
        self._set_zoom_label_text()

    def _add_button_clicked(self):
        self.select_cue(self.add_cue(Cue()))

    def _add_channel_button_pressed(self):
        """This button queries the user for a channel type and adds it to the filter and all cues.

        The default for all cues is a 0 keyframe at the start.
        """
        # TODO implement
        # TODO also think about channel type and name
        self._timeline_container.add_channel(DataType.DT_8_BIT, "Some Name")
        pass

    def _remove_channel_button_pressed(self):
        """This button queries the user for a channel to be removed and removes it from the filter output as well as
        all cues.
        """
        # TODO implement
        pass

    def rec_pressed(self):
        self._timeline_container.record_pressed()

    def jg_right(self):
        if self._jw_zoom_mode:
            self._timeline_container.increase_zoom()
        else:
            self._timeline_container.move_cursor_right()

    def jg_left(self):
        if self._jw_zoom_mode:
            self._timeline_container.decrease_zoom()
        else:
            self._timeline_container.move_cursor_left()

    def scrub_pressed(self):
        self._jw_zoom_mode = True

    def scrub_released(self):
        self._jw_zoom_mode = False

    def parent_closed(self):
        Broadcaster.desk_media_rec_pressed.disconnect(self.rec_pressed)
        Broadcaster.jogwheel_rotated_right.disconnect(self.jg_right)
        Broadcaster.jogwheel_rotated_left.disconnect(self.jg_left)
        Broadcaster.desk_media_scrub_pressed.disconnect(self.scrub_pressed)
        Broadcaster.desk_media_scrub_released.disconnect(self.scrub_released)
