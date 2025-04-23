from logging import getLogger

from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QDialog, QListWidget, QSplitter, QToolBar, QVBoxLayout, QWidget

from model import Filter
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from model.filter_data.sequencer.transition import Transition
from view.dialogs.selection_dialog import SelectionDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.channel_input_dialog import ChannelInputDialog
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (ExternalChannelDefinition,
                                                                                      PreviewEditWidget)
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__file__)


class SequencerEditor(PreviewEditWidget):

    def __init__(self, parent: QWidget = None, f: Filter | None = None):
        super().__init__(f)
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
        transition_toolbar.addAction("Link Events")
        transition_toolbar.addSeparator()
        transition_toolbar.addAction("Remove Transition")
        # TODO link actions
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
        # TODO make remaining general purpose methods (parent_closed) from cue editor reusable
        # TODO relink bankset on every changed selected transition

        self._input_dialog: QDialog | None = None

        self._selected_transition: Transition | None = None

    def _get_configuration(self) -> dict[str, str]:
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

    def get_channel_list(self) -> list[ExternalChannelDefinition]:
        l: list[ExternalChannelDefinition] = []
        for c in self._model.channels:
            ec = ExternalChannelDefinition(c.data_type, c.name, self.bs_to_channel_mapping.get(c.name), self._bankset)
            l.append(ec)
        return l

    def _transition_selected(self, new_transition: Transition | int):
        if isinstance(new_transition, int):
            new_transition = self._transition_list_widget.item(new_transition).annotated_data
        if self._selected_transition is not None:
            self._deselect_transition()
        if new_transition is not None:
            self._timeline_container.cue = new_transition.to_cue()
        else:
            self._timeline_container.cue = None
        self._selected_transition = new_transition

    def _deselect_transition(self):
        if self._selected_transition is None:
            return
        self._selected_transition.update_frames_from_cue(self._timeline_container.cue, self._model.channels)
        self._timeline_container.cue = None
        self._selected_transition = None

    def _add_transition(self, t: Transition, is_new_transition: bool = True):
        if is_new_transition:
            self._model.transitions.append(t)
        li = AnnotatedListWidgetItem(self._transition_list_widget)
        li.setText(str(self._transition_list_widget.count()))  # TODO add human readable name index to model
        li.annotated_data = t
        self._transition_list_widget.addItem(li)
        # TODO implement custom label widget that also displays linked event
        if is_new_transition:
            self._transition_selected(t)

    def _add_channel(self, c: SequencerChannel, is_new_transition: bool = True):
        if is_new_transition:
            self._model.channels.append(c)
        li = AnnotatedListWidgetItem(self._channel_list_widget)
        li.setText(f"[{c.data_type.format_for_filters()}] {c.name}")
        li.annotated_data = c
        # TODO implement custom label widget that vislualizes channel type with its default value
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
        t.preselected_channels = self._input_dialog.selected_items
        self._add_transition(t, True)

    def _populate_data(self):
        for c in self._model.channels:
            self._add_channel(c, is_new_transition=False)
        if len(self._model.transitions) > 0:
            for t in self._model.transitions:
                self._add_transition(t, is_new_transition=False)
            self._transition_selected(self._model.transitions[-1])

    def _rec_pressed(self):
        # TODO add checkboxes to timeline container to select affected channels
        pass  # TODO
