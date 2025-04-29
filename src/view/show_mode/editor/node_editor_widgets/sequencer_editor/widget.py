from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QDialog, QListWidget, QMessageBox, QSplitter, QToolBar, QVBoxLayout, QWidget

from model import Filter
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from model.filter_data.sequencer.transition import Transition
from proto import Console_pb2
from view.dialogs.selection_dialog import SelectionDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.channel_input_dialog import ChannelInputDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (ExternalChannelDefinition,
                                                                                      PreviewEditWidget)
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from PySide6.QtWidgets import QAbstractButton

    from model.filter import DataType
    from view.show_mode.editor.nodes import FilterNode


logger = getLogger(__file__)


class SequencerEditor(PreviewEditWidget):

    def __init__(self, parent: QWidget = None, f: Filter | None = None):
        super().__init__(f)
        self._timeline_container.generate_individual_frames = True
        self._parent_widget = QSplitter(parent=parent)
        self._parent_widget.setMinimumWidth(1000)
        self._parent_widget.setOrientation(Qt.Orientation.Vertical)
        self._model = SequencerFilterModel()
        settings_splitter = QSplitter(self._parent_widget)
        channel_panel = QWidget(settings_splitter)
        layout = QVBoxLayout()
        channel_toolbar = QToolBar(channel_panel)
        add_channel_action = QAction("Add Channel", channel_toolbar)
        add_channel_action.setShortcut("Ctrl+K")
        add_channel_action.triggered.connect(self._add_channel_pressed)
        channel_toolbar.addAction(add_channel_action)
        remove_channel_action = QAction("Remove Channel", channel_toolbar)
        remove_channel_action.setShortcut("Ctrl+R")
        remove_channel_action.triggered.connect(self._remove_channel_pressed)
        channel_toolbar.addAction(remove_channel_action)
        layout.addWidget(channel_toolbar)
        self._channel_list_widget = QListWidget(channel_panel)
        layout.addWidget(self._channel_list_widget)
        channel_panel.setLayout(layout)
        settings_splitter.addWidget(channel_panel)

        transition_panel = QWidget(settings_splitter)
        layout = QVBoxLayout()
        transition_toolbar = QToolBar(transition_panel)
        add_transition_action = QAction("Add Transition", transition_toolbar)
        add_transition_action.setShortcut("Ctrl+N")
        add_transition_action.triggered.connect(self._add_transition_pressed)
        transition_toolbar.addAction(add_transition_action)
        self.transition_add_channel_action = QAction("Add Channel to Transition", transition_toolbar)
        self.transition_add_channel_action.triggered.connect(self._add_channel_to_transition_pressed)
        self.transition_add_channel_action.setEnabled(False)
        transition_toolbar.addAction(self.transition_add_channel_action)
        transition_toolbar.addAction("Link Events")
        # TODO implement and link action
        transition_toolbar.addSeparator()
        self._remove_transition_action = QAction("Remove Transition", transition_toolbar)
        self._remove_transition_action.triggered.connect(self._remove_transition_clicked)
        self._remove_transition_action.setEnabled(False)
        transition_toolbar.addAction(self._remove_transition_action)
        layout.addWidget(transition_toolbar)
        self._transition_list_widget = QListWidget(transition_panel)
        self._transition_list_widget.currentRowChanged.connect(self._transition_selected)
        layout.addWidget(self._transition_list_widget)
        transition_panel.setLayout(layout)
        settings_splitter.addWidget(transition_panel)
        self._parent_widget.addWidget(settings_splitter)

        timeline_panel = QWidget(self._parent_widget)
        layout = QVBoxLayout()
        timeline_toolbar = QToolBar(timeline_panel)
        timeline_toolbar.addWidget(self.transition_type_select_widget)
        timeline_toolbar.addAction(self._gui_rec_action)
        timeline_toolbar.addWidget(self.zoom_panel)
        layout.addWidget(timeline_toolbar)
        layout.addWidget(self._timeline_container)
        timeline_panel.setLayout(layout)
        self._parent_widget.addWidget(timeline_panel)
        self._parent_widget.setStretchFactor(1, 3)
        # TODO add checkboxes to timeline container to select affected channels

        self._input_dialog: QDialog | None = None
        self._selected_transition: Transition | None = None

    def _get_configuration(self) -> dict[str, str]:
        if self._selected_transition is not None:
            self._selected_transition.update_frames_from_cue(self._timeline_container.cue, self._model.channels)
        return self._model.get_configuration()

    def _load_configuration(self, conf: dict[str, str]):
        self._model.load_configuration(conf)
        self._populate_data()

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        pass  # Nothing to do here

    def _get_parameters(self) -> dict[str, str]:
        return {}

    def _get_model_channels(self) -> list[tuple[str, "DataType"]]:
        l = []
        for c in self._model.channels:
            l.append((c.name, c.data_type))
        return l

    def get_channel_list(self) -> list[ExternalChannelDefinition]:
        l: list[ExternalChannelDefinition] = []
        for c in self._model.channels:
            ec = ExternalChannelDefinition(c.data_type, c.name, self.bs_to_channel_mapping.get(c.name), self._bankset)
            l.append(ec)
        return l

    def _transition_selected(self, new_transition: Transition | int | None):
        if isinstance(new_transition, int):
            logger.info("Looking up transition %i.", new_transition)
            item = self._transition_list_widget.item(new_transition)
            if item is not None:
                new_transition = item.annotated_data
            else:
                new_transition = None
        if self._selected_transition is not None:
            self._deselect_transition()
        if new_transition is not None:
            self._timeline_container.cue = new_transition.to_cue()
            self._remove_transition_action.setEnabled(True)
            self.set_editing_enabled(True)
            self.transition_add_channel_action.setEnabled(True)
        else:
            self._timeline_container.cue = None
            self._remove_transition_action.setEnabled(False)
            self.set_editing_enabled(False)
            self.transition_add_channel_action.setEnabled(False)
        self._selected_transition = new_transition
        self._recolor_bankset()

    def _deselect_transition(self):
        if self._selected_transition is None:
            return
        self._selected_transition.update_frames_from_cue(self._timeline_container.cue, self._model.channels)
        self._timeline_container.cue = None
        self._selected_transition = None
        self._remove_transition_action.setEnabled(False)
        self.set_editing_enabled(False)
        self.transition_add_channel_action.setEnabled(False)

    def _add_transition(self, t: Transition, is_new_transition: bool = True):
        if is_new_transition:
            self._model.transitions.append(t)
        li = AnnotatedListWidgetItem(self._transition_list_widget)
        li.setText(str(self._transition_list_widget.count()))  # TODO add human readable name index to model
        li.annotated_data = t
        self._transition_list_widget.addItem(li)
        # TODO implement custom label widget that also displays linked events and duration
        # TODO write widget in map with k=transition and v=widget
        if is_new_transition or self._selected_transition is None:
            self._transition_selected(t)

    def _add_channel(self, c: SequencerChannel, is_new_transition: bool = True):
        if is_new_transition:
            self._model.append_channel(c)
        li = AnnotatedListWidgetItem(self._channel_list_widget)
        li.setText(f"[{c.data_type.format_for_filters()}] {c.name}")
        li.annotated_data = c
        # TODO implement custom label widget that vislualizes channel type with its default value
        if self._filter_instance is not None:
            if self._filter_instance.in_preview_mode:
                self.link_column_to_channel(c.name, c.data_type, not is_new_transition)
        self._channel_list_widget.addItem(li)

    def _add_channel_pressed(self):
        self._input_dialog = ChannelInputDialog(self._parent_widget, lambda name, dtype: self._add_channel(SequencerChannel(name=name, dtype=dtype)))
        self._input_dialog.show()

    def _remove_channel_pressed(self):
        self._input_dialog = SelectionDialog("Remove Channels", "Please select Channels to remove.",
                                             [c.name for c in self._model.channels], self._parent_widget)
        self._input_dialog.accepted.connect(self._remove_channels_button_pressed_final)
        self._input_dialog.show()

    def _remove_channels_button_pressed_final(self):
        if not isinstance(self._input_dialog, SelectionDialog):
            return
        orig_t = self._selected_transition
        self._deselect_transition()
        channels_to_remove = self._input_dialog.selected_items
        self._model.remove_channels(channels_to_remove)
        items_to_remove = []
        for item_index in range(self._channel_list_widget.count()):
            item = self._channel_list_widget.item(item_index)
            if not isinstance(item, AnnotatedListWidgetItem):
                continue
            if item.annotated_data.name in channels_to_remove:
                items_to_remove.append(item)
        for item in items_to_remove:
            self._channel_list_widget.takeItem(self._channel_list_widget.row(item))
        self._transition_selected(orig_t)
        self._input_dialog.deleteLater()

    def _add_transition_pressed(self):
        self._input_dialog = SelectionDialog("Select Channels",
                                             "Please select Channels to add in the new transition.",
                                             [c.name for c in self._model.channels], self._parent_widget)
        self._input_dialog.accepted.connect(self._add_transition_pressed_final)
        self._input_dialog.show()

    def _add_transition_pressed_final(self):
        t = Transition()
        if not isinstance(self._input_dialog, SelectionDialog):
            logger.error("Expected SelectionDialog.")
            return
        channel_dict = {}
        for c_name in self._input_dialog.selected_items:
            channel_dict[c_name] = self._model.get_channel_by_name(c_name).data_type
        t.preselected_channels = channel_dict
        self._add_transition(t, True)
        self._input_dialog.deleteLater()

    def _add_channel_to_transition_pressed(self):
        channels_avail = []
        existing_channel_names = self._selected_transition.preselected_channels.keys()
        for c in self._model.channels:
            channel_name = c.name
            if channel_name in existing_channel_names:
                continue
            channels_avail.append(channel_name)
        self._input_dialog = SelectionDialog("Select Channels",
                                             "Please select Channels to add in the existing transition.",
                                             channels_avail, self._parent_widget)
        self._input_dialog.accepted.connect(self._add_channel_to_transition_pressed_final)
        self._input_dialog.show()

    def _add_channel_to_transition_pressed_final(self):
        if self._selected_transition is None:
            logger.error("No transition selected while adding channels to it.")
            return
        if not isinstance(self._input_dialog, SelectionDialog):
            logger.error("Expected SelectionDialog.")
            return
        channel_dict: dict[str, DataType] = {}
        for c_name in self._input_dialog.selected_items:
            channel_dict[c_name] = self._model.get_channel_by_name(c_name).data_type
        self._selected_transition.preselected_channels.update(channel_dict)
        self._transition_selected(self._selected_transition)

    def _remove_transition_clicked(self):
        self._input_dialog = QMessageBox(self._parent_widget)
        self._input_dialog.setModal(True)
        self._input_dialog.setWindowTitle("Delete Transition")
        self._input_dialog.setText("Do you really want to delete this transition?")
        self._input_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Abort)
        self._input_dialog.setIcon(QMessageBox.Icon.Warning)
        self._input_dialog.buttonClicked.connect(self._remove_transition_final)
        self._input_dialog.show()

    def _remove_transition_final(self, button: "QAbstractButton"):
        if not isinstance(self._input_dialog, QMessageBox):
            logger.error("Expected message box as delete dialog.")
            return
        if self._input_dialog.buttonRole(button) == QMessageBox.ButtonRole.YesRole:
            if self._selected_transition is not None:
                self._model.transitions.remove(self._selected_transition)
                items_to_remove = []
                for item_index in range(self._transition_list_widget.count()):
                    item = self._transition_list_widget.item(item_index)
                    if not isinstance(item, AnnotatedListWidgetItem):
                        continue
                    if item.annotated_data == self._selected_transition:
                        items_to_remove.append(item)
                for item in items_to_remove:
                    self._transition_list_widget.takeItem(self._transition_list_widget.row(item))
                self._deselect_transition()
        self._input_dialog.deleteLater()

    def _recolor_bankset(self):
        if self._bankset is None:
            return
        active_channels: set[str] = set()
        if self._timeline_container.cue is not None:
            for c in self._timeline_container.cue.channels:
                active_channels.add(c.name)
        for channel in self.channels:
            if channel.fader is None:
                continue
            if channel.name in active_channels:
                channel.fader.display_color = Console_pb2.lcd_color.white
            else:
                channel.fader.display_color = Console_pb2.lcd_color.black
            channel.fader.update()

    def _populate_data(self):
        for c in self._model.channels:
            self._add_channel(c, is_new_transition=False)
        if len(self._model.transitions) > 0:
            for t in self._model.transitions:
                self._add_transition(t, is_new_transition=False)
            self._transition_selected(self._model.transitions[-1])

    def _rec_pressed(self):
        super()._rec_pressed()
        # TODO update duration label of transition

    def parent_opened(self):
        self._input_dialog = YesNoDialog(self.get_widget(), self._link_bankset)
