from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QScrollArea, QHBoxLayout, QTableWidget, \
    QTableWidgetItem, QFormLayout, QComboBox, QCheckBox, QPushButton, QLabel, QInputDialog, QAbstractItemView, \
    QMessageBox, QDialog

from model import DataType
from model.broadcaster import Broadcaster
from model.control_desk import BankSet, FaderBank, ColorDeskColumn, RawDeskColumn
from view.show_mode.node_editor_widgets.cue_editor.channel_input_dialog import ChannelInputDialog
from view.show_mode.node_editor_widgets.cue_editor.cue import Cue, EndAction, StateColor, StateEightBit, StateDouble, \
    StateSixteenBit
from view.show_mode.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.node_editor_widgets.node_editor_widget import NodeEditorFilterConfigWidget
from view.show_mode.nodes import FilterNode


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
        self._global_restart_on_end = parameters.get("end_handling") == "start_again"
        mapping_str = parameters.get("mapping")
        cuelist_definition_str = parameters.get("cuelist")
        if cuelist_definition_str:
            cue_definitions = cuelist_definition_str.split("$")
        else:
            return
        for i in range(len(cue_definitions)):
            self.add_cue(Cue())
        if mapping_str:
            for channel_dev in mapping_str.split(';'):
                splitted_channel_dev = channel_dev.split(':')
                self._add_channel(splitted_channel_dev[0], DataType.from_filter_str(splitted_channel_dev[1]),
                                  is_part_of_mass_update=True)
        for i in range(len(cue_definitions)):
            self._cues[i].from_string_definition(cue_definitions[i])
            self._cue_list_widget.item(self._cues[i].index_in_editor - 1, 1).setText(self._cues[i].duration_formatted)
            self._cue_list_widget.item(self._cues[i].index_in_editor - 1, 2).setText(str(self._cues[i].end_action))
        if len(self._cues) > 0:
            self.select_cue(0)
        if self._bankset:
            self._bankset.update()
            BankSet.push_messages_now()

    def _get_parameters(self) -> dict[str, str]:
        if len(self._cues) > 0:
            mapping_str = ";".join(["{}:{}".format(t[0], t[1].format_for_filters()) for t in self._cues[0].channels])
        else:
            mapping_str = ""
        d = {
            "end_handling": "start_again" if self._global_restart_on_end else "hold",
            "mapping": mapping_str,
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
        self._cue_list_widget.verticalHeader().hide()
        self._cue_list_widget.itemSelectionChanged.connect(self._cue_list_selection_changed)
        self._cue_list_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        cue_list_and_current_settings_container_layout.addWidget(self._cue_list_widget)
        cue_settings_container = QWidget(parent=self._parent_widget)
        cue_settings_container_layout = QFormLayout()
        self._current_cue_end_action_select_widget = QComboBox(cue_settings_container)
        self._current_cue_end_action_select_widget.addItems(EndAction.formatted_value_list())
        self._current_cue_end_action_select_widget.setEnabled(False)
        self._current_cue_end_action_select_widget.currentIndexChanged.connect(self._cue_end_action_changed)
        cue_settings_container_layout.addRow("End Action", self._current_cue_end_action_select_widget)
        self._current_cue_another_play_pressed_checkbox = QCheckBox("Restart cue on Play pressed", self._parent_widget)
        self._current_cue_another_play_pressed_checkbox.clicked.connect(self._cue_play_pressed_restart_changed)
        self._current_cue_another_play_pressed_checkbox.setEnabled(False)
        cue_settings_container_layout.addRow("", self._current_cue_another_play_pressed_checkbox)

        self._zoom_label: QLabel | None = None
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
        self._timeline_container.setEnabled(False)
        v_scroll_area.setWidget(self._timeline_container)
        top_layout.addWidget(v_scroll_area)
        self._parent_widget.setLayout(top_layout)
        self._jw_zoom_mode = False

        self._broadcaster: Broadcaster = None
        self._bankset: BankSet = None
        self._input_dialog: QDialog = None

        self._set_zoom_label_text()
        self._global_restart_on_end: bool = False
        self._cues: list[Cue] = []
        self._last_selected_cue = -1

    def _link_bankset(self):
        self._broadcaster = Broadcaster()
        self._broadcaster.desk_media_rec_pressed.connect(self._rec_pressed)
        self._broadcaster.jogwheel_rotated_right.connect(self.jg_right)
        self._broadcaster.jogwheel_rotated_left.connect(self.jg_left)
        self._broadcaster.desk_media_scrub_pressed.connect(self.scrub_pressed)
        self._broadcaster.desk_media_scrub_released.connect(self.scrub_released)
        self._bankset = BankSet(gui_controlled=True)
        self._bankset.description = "Cue Editor BS"
        self._bankset.link()
        self._bankset.activate()
        self._timeline_container.bankset = self._bankset
        for c in self._timeline_container.cue.channels:
            self._link_column_to_channel(c[0], c[1], True)
        self._bankset.update()
        BankSet.push_messages_now()

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
        toolbar_add_cue_action.triggered.connect(self._add_cue_button_clicked)
        toolbar.addAction(toolbar_add_cue_action)
        self._toolbar_add_channel_action = QAction("Add Channel", self._parent_widget)
        self._toolbar_add_channel_action.setEnabled(False)
        self._toolbar_add_channel_action.setStatusTip("Add a new channel to the filter")
        self._toolbar_add_channel_action.triggered.connect(self._add_channel_button_pressed)
        toolbar.addAction(self._toolbar_add_channel_action)
        toolbar_remove_channel_action = QAction("Remove Channel", self._parent_widget)
        toolbar_remove_channel_action.setStatusTip("Removes a channel from the filter")
        toolbar_remove_channel_action.setEnabled(False)
        toolbar_remove_channel_action.triggered.connect(self._remove_channel_button_pressed)
        toolbar.addAction(toolbar_remove_channel_action)
        toolbar.addSeparator()
        transition_type_select_widget = QComboBox(self._parent_widget)
        transition_type_select_widget.addItems(["edg", "lin", "sig", "e_i", "e_o"])
        transition_type_select_widget.currentTextChanged.connect(self._transition_type_changed)
        toolbar.addWidget(transition_type_select_widget)
        self._gui_rec_action = QAction("Record keyframe", self._parent_widget)
        self._gui_rec_action.setStatusTip("Insert a Keyframe at the current cursor position")
        self._gui_rec_action.setIcon(QIcon.fromTheme("media-record"))
        self._gui_rec_action.setEnabled(False)
        self._gui_rec_action.triggered.connect(self._rec_pressed)
        toolbar.addAction(self._gui_rec_action)
        top_layout.addWidget(toolbar)

    def _set_zoom_label_text(self):
        self._zoom_label.setText(self._timeline_container.format_zoom())

    def add_cue(self, cue: Cue) -> int:
        target_row = self._cue_list_widget.rowCount()
        self._cue_list_widget.setRowCount(target_row + 1)
        num_item = QTableWidgetItem(1)
        num_item.setText(str(target_row + 1))
        self._cue_list_widget.setItem(target_row, 0, num_item)
        duration_item = QTableWidgetItem(1)
        duration_item.setText(cue.duration_formatted)
        self._cue_list_widget.setItem(target_row, 1, duration_item)
        end_action_item = QTableWidgetItem(1)
        end_action_item.setText(str(cue.end_action))
        self._cue_list_widget.setItem(target_row, 2, end_action_item)
        if len(self._cues) > 0:
            for c in self._cues[0].channels:
                cue.add_channel(c[0], c[1])
        cue.index_in_editor = target_row + 1
        self._cues.append(cue)
        return target_row

    def select_cue(self, cue_index: int, from_manual_input: bool = False):
        if cue_index < 0 or cue_index >= len(self._cues):
            return
        if 0 <= self._last_selected_cue < len(self._cues):
            self._cues[self._last_selected_cue] = self._timeline_container.cue
        c = self._cues[cue_index]
        self._timeline_container.cue = c
        self._current_cue_end_action_select_widget.setCurrentIndex(c.end_action.value)
        self._current_cue_another_play_pressed_checkbox.setChecked(c.restart_on_another_play_press)
        if from_manual_input:
            self._cue_list_widget.selectRow(cue_index)
        self._toolbar_add_channel_action.setEnabled(True)
        self._timeline_container.setEnabled(True)
        self._current_cue_end_action_select_widget.setEnabled(True)
        self._gui_rec_action.setEnabled(True)
        self._current_cue_another_play_pressed_checkbox.setEnabled(True)

    def _cue_list_selection_changed(self):
        items_list = self._cue_list_widget.selectedIndexes()
        if len(items_list) > 0:
            self.select_cue(items_list[0].row(), from_manual_input=False)
        else:
            self._cue_list_widget.selectRow(self._last_selected_cue)

    def increase_zoom(self):
        self._timeline_container.increase_zoom()
        self._set_zoom_label_text()

    def decrease_zoom(self):
        self._timeline_container.decrease_zoom()
        self._set_zoom_label_text()

    def _add_cue_button_clicked(self):
        new_index = self.add_cue(Cue())
        self.select_cue(new_index)

    def _add_channel_button_pressed(self):
        """This button queries the user for a channel type and adds it to the filter and all cues.

        The default for all cues is a 0 keyframe at the start.
        """
        self._input_dialog = ChannelInputDialog(self._parent_widget, self._add_channel)
        self._input_dialog.show()

    def _add_channel(self, channel_name: str, channel_type: DataType, is_part_of_mass_update: bool = False):
        if channel_name == "time":
            QMessageBox.critical(self._parent_widget, "Failed to add channel",
                                 "Unfortunately, 'time' is a reserved keyword for this filter.")
            return
        for c_name in self._cues[0].channels:
            if c_name[0] == channel_name:
                QMessageBox.critical(self._parent_widget, "Failed to add channel",
                                     "Unable to add the requested channel {}. Channel names must be unique within "
                                     "this filter.".format(channel_name))
                return
        self._link_column_to_channel(channel_name, channel_type, is_part_of_mass_update)
        for c in self._cues:
            c.add_channel(channel_name, channel_type)
            for kf in c._frames:
                match channel_type:
                    case DataType.DT_COLOR:
                        kf_s = StateColor("edg")
                    case DataType.DT_8_BIT:
                        kf_s = StateEightBit("edg")
                    case DataType.DT_DOUBLE:
                        kf_s = StateDouble("edg")
                    case DataType.DT_16_BIT:
                        kf_s = StateSixteenBit("edg")
                    case _:
                        kf_s = StateEightBit("edg")
                kf._states.append(kf_s)
        self._timeline_container.add_channel(channel_type, channel_name)
        BankSet.push_messages_now()

    def _link_column_to_channel(self, channel_name, channel_type, is_part_of_mass_update):
        if not self._bankset:
            return
        if channel_type == DataType.DT_COLOR:
            c = ColorDeskColumn()
        else:
            c = RawDeskColumn()
        c.display_name = channel_name
        self._bankset.add_column_to_next_bank(c)
        if not is_part_of_mass_update:
            self._bankset.update()

    def _remove_channel_button_pressed(self):
        """This button queries the user for a channel to be removed and removes it from the filter output as well as
        all cues.
        """
        # TODO implement
        pass

    def _cue_end_action_changed(self):
        action = EndAction(self._current_cue_end_action_select_widget.currentIndex())
        self._timeline_container.cue.end_action = action
        self._cue_list_widget.item(self._timeline_container.cue.index_in_editor - 1, 2).setText(str(action))

    def _cue_play_pressed_restart_changed(self):
        self._timeline_container.cue.restart_on_another_play_press = \
            self._current_cue_another_play_pressed_checkbox.checkState()

    def _transition_type_changed(self, text):
        self._timeline_container.transition_type = text

    def _rec_pressed(self):
        self._timeline_container.record_pressed()
        self._cue_list_widget.item(self._timeline_container.cue.index_in_editor - 1, 1) \
            .setText(self._timeline_container.cue.duration_formatted)

    def jg_right(self):
        if self._jw_zoom_mode:
            self._timeline_container.increase_zoom(1.25)
            self._set_zoom_label_text()
        else:
            self._timeline_container.move_cursor_right()

    def jg_left(self):
        if self._jw_zoom_mode:
            self._timeline_container.decrease_zoom(1.25)
            self._set_zoom_label_text()
        else:
            self._timeline_container.move_cursor_left()

    def scrub_pressed(self):
        self._jw_zoom_mode = True

    def scrub_released(self):
        self._jw_zoom_mode = False

    def parent_closed(self, filter_node: FilterNode):
        self._timeline_container.clear_display()
        filter_node.clearTerminals()
        filter_node.addTerminal('time', io='in')
        if len(self._cues) > 0:
            for channel_name, channel_type in self._cues[0].channels:
                filter_node.addTerminal(channel_name, io='out')
        if self._bankset:
            self._bankset.unlink()
            BankSet.push_messages_now()
        if self._broadcaster:
            self._broadcaster.desk_media_rec_pressed.disconnect(self._rec_pressed)
            self._broadcaster.jogwheel_rotated_right.disconnect(self.jg_right)
            self._broadcaster.jogwheel_rotated_left.disconnect(self.jg_left)
            self._broadcaster.desk_media_scrub_pressed.disconnect(self.scrub_pressed)
            self._broadcaster.desk_media_scrub_released.disconnect(self.scrub_released)

    def parent_opened(self):
        self._input_dialog = YesNoDialog(self.get_widget(), self._link_bankset)
