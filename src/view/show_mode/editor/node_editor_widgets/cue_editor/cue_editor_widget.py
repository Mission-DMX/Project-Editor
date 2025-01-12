from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QScrollArea, QHBoxLayout, QTableWidget, \
    QTableWidgetItem, QFormLayout, QComboBox, QCheckBox, QPushButton, QLabel, QAbstractItemView, \
    QMessageBox, QDialog, QMenu

from controller.file.transmitting_to_fish import transmit_to_fish
from model import DataType, Filter
from model.broadcaster import Broadcaster
from model.control_desk import BankSet, ColorDeskColumn, RawDeskColumn, DeskColumn
from model.virtual_filters.cue_vfilter import CueFilter
from view.dialogs.selection_dialog import SelectionDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.channel_input_dialog import ChannelInputDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import Cue, EndAction
from view.show_mode.editor.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from .model.cue_filter_model import CueFilterModel
from ..node_editor_widget import NodeEditorFilterConfigWidget


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from view.show_mode.editor.nodes.base.filternode import FilterNode


class ExternalChannelDefinition:
    """In case we're in preview mode we need to instantiate filters for the preview based on this information.

    As I didn't want to write a tuple of the channel name, its type as well as fader source, this class provides them
    in a named fashion.
    """
    def __init__(self, data_type: DataType, name: str, associated_fader: DeskColumn, bank_set: BankSet):
        self.data_type = data_type
        self.name = name
        self.fader = associated_fader
        self.bankset = bank_set


class CueEditor(NodeEditorFilterConfigWidget):

    def _get_parameters(self) -> dict[str, str]:
        # TODO implement
        return dict()

    def _load_parameters(self, conf: dict[str, str]):
        # TODO implement
        pass

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_configuration(self, parameters: dict[str, str]):
        self._model.load_from_configuration(parameters)

        for c in self._model.cues:
            self.add_cue(c, name=c.name)
            self._cue_list_widget.item(c.index_in_editor - 1, 1).setText(c.duration_formatted)
            self._cue_list_widget.item(c.index_in_editor - 1, 2).setText(str(c.end_action))

        for name, dt in self._model.channels:
            self._add_channel(name, dt, is_part_of_mass_update=True)

        if len(self._model.cues) > 0:
            self.select_cue(0)
            self._default_cue_combo_box.setEnabled(True)
        self._default_cue_combo_box.setCurrentIndex(self._model.default_cue)
        if self._bankset:
            self._bankset.update()
            BankSet.push_messages_now()

    def _get_configuration(self) -> dict[str, str]:
        self._model.default_cue = self._default_cue_combo_box.currentIndex() - 1
        return self._model.get_as_configuration()

    def __init__(self, parent: QWidget = None, f: Filter | None = None):
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
        self._cue_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._cue_list_widget.customContextMenuRequested.connect(self._table_context_popup)
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
        self._setup_zoom_panel(cue_settings_container, cue_settings_container_layout)
        cue_settings_container.setLayout(cue_settings_container_layout)
        cue_list_and_current_settings_container_layout.addWidget(cue_settings_container)

        self._default_cue_combo_box = QComboBox(cue_settings_container)
        self._default_cue_combo_box.addItem("No default Cue")
        self._default_cue_combo_box.setEnabled(False)
        cue_settings_container_layout.addWidget(self._default_cue_combo_box)

        cue_list_and_current_settings_container.setLayout(cue_list_and_current_settings_container_layout)
        cue_list_and_current_settings_container.setMaximumHeight(350)
        top_layout.addWidget(cue_list_and_current_settings_container)

        self._configure_toolbar(top_layout)

        v_scroll_area = QScrollArea()
        v_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        v_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        v_scroll_area.horizontalScrollBar().setEnabled(False)
        v_scroll_area.setWidgetResizable(True)
        # TODO link up/down button events to scrolling of v_scroll_area
        self._timeline_container = TimelineContainer(v_scroll_area)
        self._timeline_container.setEnabled(False)
        self._timeline_container.transition_type = "lin"
        v_scroll_area.setWidget(self._timeline_container)
        top_layout.addWidget(v_scroll_area)
        self._parent_widget.setLayout(top_layout)
        self._jw_zoom_mode = False

        self._broadcaster: Broadcaster = None
        self._bankset: BankSet = None
        self._input_dialog: QDialog = None

        self._set_zoom_label_text()
        self._model = CueFilterModel()
        self._bs_to_channel_mapping: dict[str, DeskColumn] = {}
        self._filter_instance = f if isinstance(f, CueFilter) else None
        self._last_selected_cue = -1
        self._channels_changed_after_load = False
        self._broadcaster_signals_connected = False

        if self._filter_instance:
            self._filter_instance.associated_editor_widget = self

    def _link_bankset(self):
        self._broadcaster = Broadcaster()
        self._broadcaster.desk_media_rec_pressed.connect(self._rec_pressed)
        self._broadcaster.jogwheel_rotated_right.connect(self.jg_right)
        self._broadcaster.jogwheel_rotated_left.connect(self.jg_left)
        self._broadcaster.desk_media_scrub_pressed.connect(self.scrub_pressed)
        self._broadcaster.desk_media_scrub_released.connect(self.scrub_released)
        self._broadcaster_signals_connected = True
        self._bankset = BankSet(gui_controlled=True)
        self._bankset.description = "Cue Editor BS"
        self._bankset.link()
        self._bankset.activate()
        self._timeline_container.bankset = self._bankset
        for c in self._timeline_container.cue.channels:
            self._link_column_to_channel(c[0], c[1], True)
        self._bankset.update()
        BankSet.push_messages_now()
        if self._filter_instance:
            self._filter_instance.in_preview_mode = True
            transmit_to_fish(self._filter_instance.scene.board_configuration, False)
            # TODO switch to scene of filter

    def _setup_zoom_panel(self, cue_settings_container, cue_settings_container_layout):
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

    def _configure_toolbar(self, top_layout):
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
        self._toolbar_remove_channel_action = QAction("Remove Channel", self._parent_widget)
        self._toolbar_remove_channel_action.setStatusTip("Removes a channel from the filter")
        self._toolbar_remove_channel_action.setEnabled(False)
        self._toolbar_remove_channel_action.triggered.connect(self._remove_channel_button_pressed)
        toolbar.addAction(self._toolbar_remove_channel_action)
        toolbar.addSeparator()
        transition_type_select_widget = QComboBox(self._parent_widget)
        transition_type_select_widget.addItems(["lin", "edg", "sig", "e_i", "e_o"])
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

    def _table_context_popup(self, pos):
        self._input_dialog = QMenu()
        self._input_dialog.addAction(QIcon.fromTheme("edit-paste"), "Duplicate", self._duplicate_cue_clicked)
        self._input_dialog.addAction(QIcon.fromTheme("go-up"), "Move Up", self._move_cue_up_clicked)
        self._input_dialog.addAction(QIcon.fromTheme("go-down"), "Move Down", self._move_cue_down_clicked)
        self._input_dialog.setEnabled(len(self._model.cues) > 0)
        pos = self._cue_list_widget.mapToGlobal(pos)
        self._input_dialog.popup(pos, None)

    def _indices_from_table_selection(self, ascending_order: bool = True) -> list[int]:
        selected_items = self._cue_list_widget.selectedItems()
        processed_indices = []
        for item in selected_items:
            index = item.row()
            if index in processed_indices:
                continue
            processed_indices.append(index)
        processed_indices.sort(reverse=not ascending_order)
        return processed_indices

    def _duplicate_cue_clicked(self):
        for index in self._indices_from_table_selection():
            new_cue = self._model.cues[index].copy()
            self.add_cue(new_cue, new_cue.name)

    def _swap_table_rows(self, i1: int, i2: int):
        row1: list[tuple[QTableWidgetItem, int]] = []
        row2: list[tuple[QTableWidgetItem, int]] = []
        for column_index in range(self._cue_list_widget.columnCount()):
            row1.append((self._cue_list_widget.takeItem(i1, column_index), column_index))
            row2.append((self._cue_list_widget.takeItem(i2, column_index), column_index))
        for item in row1:
            self._cue_list_widget.setItem(i2, item[1], item[0])
        for item in row2:
            self._cue_list_widget.setItem(i1, item[1], item[0])

    def _move_cue_up_clicked(self):
        for index in self._indices_from_table_selection():
            if index == 0:
                continue
            old_cue = self._model.cues[index - 1]
            self._model.cues[index - 1] = self._model.cues[index]
            self._model.cues[index] = old_cue
            self._swap_table_rows(index - 1, index)

    def _move_cue_down_clicked(self):
        for index in self._indices_from_table_selection():
            if index >= self._cue_list_widget.rowCount() - 1:
                continue
            old_cue = self._model.cues[index + 1]
            self._model.cues[index + 1] = self._model.cues[index]
            self._model.cues[index] = old_cue
            self._swap_table_rows(index + 1, index)

    def add_cue(self, cue: Cue, name: str | None = None) -> int:
        target_row = self._cue_list_widget.rowCount()
        self._cue_list_widget.setRowCount(target_row + 1)
        num_item = QTableWidgetItem(1)
        cue_name = "{} '{}'".format(target_row + 1, name)
        num_item.setText(cue_name)
        # TODO connect name changing property here
        self._cue_list_widget.setItem(target_row, 0, num_item)
        duration_item = QTableWidgetItem(1)
        duration_item.setText(cue.duration_formatted)
        duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._cue_list_widget.setItem(target_row, 1, duration_item)
        end_action_item = QTableWidgetItem(1)
        end_action_item.setText(str(cue.end_action))
        end_action_item.setFlags(end_action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._cue_list_widget.setItem(target_row, 2, end_action_item)
        if len(self._model.cues) > 0:
            for c in self._model.cues[0].channels:
                cue.add_channel(c[0], c[1])
        cue.index_in_editor = target_row + 1
        self._model.append_cue(cue)
        self._default_cue_combo_box.addItem("Cue {}".format(cue_name))
        self._default_cue_combo_box.setEnabled(True)
        return target_row

    def select_cue(self, cue_index: int, from_manual_input: bool = False):
        if cue_index < 0 or cue_index >= len(self._model.cues):
            return
        if 0 <= self._last_selected_cue < len(self._model.cues):
            self._model.cues[self._last_selected_cue] = self._timeline_container.cue
        c = self._model.cues[cue_index]
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
        if channel_name == "time" or channel_name == "time_scale":
            QMessageBox.critical(self._parent_widget, "Failed to add channel",
                                 "Unfortunately, 'time' and 'time_scale' is a reserved keyword for this filter.")
            return
        try:
            self._model.add_channel(channel_name, channel_type)
        except ValueError as e:
            QMessageBox.critical(self._parent_widget, "Failed to add channel",
                                 "Unable to add the requested channel {}. Channel names must be unique within "
                                 "this filter.<br/>Detailed message: {}".format(channel_name, str(e)))
            return
        if self._filter_instance.in_preview_mode:
            self._link_column_to_channel(channel_name, channel_type, is_part_of_mass_update)
        self._timeline_container.add_channel(channel_type, channel_name)
        BankSet.push_messages_now()
        if not is_part_of_mass_update:
            self._channels_changed_after_load = True
        self._toolbar_remove_channel_action.setEnabled(True)

    def _link_column_to_channel(self, channel_name, channel_type, is_part_of_mass_update):
        if not self._bankset:
            return
        if channel_type == DataType.DT_COLOR:
            c = ColorDeskColumn()
        else:
            c = RawDeskColumn()
        c.display_name = channel_name
        self._bankset.add_column_to_next_bank(c)
        self._bs_to_channel_mapping[channel_name] = c
        if not is_part_of_mass_update:
            self._bankset.update()

    def _remove_channel_button_pressed(self):
        """This button queries the user for a channel to be removed and removes it from the filter output as well as
        all cues.
        """
        self._input_dialog = SelectionDialog("Remove Channels", "Please select Channels to remove.",
                                             [c[0] for c in self._model.channels], self._parent_widget)
        self._input_dialog.accepted.connect(self._remove_channels_button_pressed_final)
        self._input_dialog.show()

    def _remove_channels_button_pressed_final(self):
        if not isinstance(self._input_dialog, SelectionDialog):
            return
        selected_channels = self._input_dialog.selected_items
        channels_to_remove = []
        for c in self._model.channels:
            if c[0] in selected_channels:
                channels_to_remove.append(c)
                self._timeline_container.remove_channel(c[0])
        for c in channels_to_remove:
            self._model.remove_channel(c)
        if len(channels_to_remove) > 0:
            self._channels_changed_after_load = True
        self._toolbar_remove_channel_action.setEnabled(len(self._model.cues) > 0 and len(self._model.channels) > 0)

    def _cue_end_action_changed(self):
        action = EndAction(self._current_cue_end_action_select_widget.currentIndex())
        self._timeline_container.cue.end_action = action
        self._cue_list_widget.item(self._timeline_container.cue.index_in_editor - 1, 2).setText(str(action))

    def _cue_play_pressed_restart_changed(self):
        self._timeline_container.cue.restart_on_another_play_press = \
            self._current_cue_another_play_pressed_checkbox.checkState().Checked

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

    def parent_closed(self, filter_node: "FilterNode"):
        self._timeline_container.clear_display()
        if self._channels_changed_after_load:
            added_channels = []
            if len(self._model.cues) > 0:
                for channel_name, channel_type in self._model.cues[0].channels:
                    if channel_name not in filter_node.outputs():
                        filter_node.addTerminal(channel_name, io='out')
                        filter_node.filter.out_data_types[channel_name] = channel_type
                    added_channels.append(channel_name)
            terms_to_remove = []
            for name, term in filter_node.terminals.items():
                if name in filter_node.outputs() and name not in added_channels:
                    terms_to_remove.append(name)
            for name in terms_to_remove:
                filter_node.removeTerminal(name)
        if self._bankset:
            self._bankset.unlink()
            BankSet.push_messages_now()
        show_reset_required = False
        if self._broadcaster and self._broadcaster_signals_connected:
            self._broadcaster.desk_media_rec_pressed.disconnect(self._rec_pressed)
            self._broadcaster.jogwheel_rotated_right.disconnect(self.jg_right)
            self._broadcaster.jogwheel_rotated_left.disconnect(self.jg_left)
            self._broadcaster.desk_media_scrub_pressed.disconnect(self.scrub_pressed)
            self._broadcaster.desk_media_scrub_released.disconnect(self.scrub_released)
            self._broadcaster_signals_connected = False
            show_reset_required = True
        if self._filter_instance:
            self._filter_instance.in_preview_mode = False
            if show_reset_required:
                transmit_to_fish(self._filter_instance.scene.board_configuration, False)
                # TODO switch to scene of filter
        super().parent_closed(filter_node)

    def parent_opened(self):
        self._input_dialog = YesNoDialog(self.get_widget(), self._link_bankset)

    @property
    def channels(self) -> list[ExternalChannelDefinition]:
        channel_list = []
        # it should be sufficient to only check the fist cue as all cues should have the same channels
        if len(self._model.cues) == 0:
            return channel_list
        for name, c_type in self._model.cues[0].channels:
            channel_list.append(ExternalChannelDefinition(c_type, name,
                                                          self._bs_to_channel_mapping.get(name), self._bankset))
        return channel_list
