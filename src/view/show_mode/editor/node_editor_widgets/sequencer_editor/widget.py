from PySide6.QtWidgets import QListWidget, QSplitter, QToolBar, QVBoxLayout, QWidget

from model import Filter
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from model.filter_data.sequencer.transition import Transition
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (ExternalChannelDefinition,
                                                                                      PreviewEditWidget)
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem


class SequencerEditor(PreviewEditWidget):

    def __init__(self, parent: QWidget = None, f: Filter | None = None):
        super().__init__()
        self._parent_widget = QSplitter(parent=parent)
        self._parent_widget.setMinimumWidth(1000)
        self._model = SequencerFilterModel()
        channel_panel = QWidget(self._parent_widget)
        layout = QVBoxLayout()
        channel_toolbar = QToolBar(channel_panel)
        channel_toolbar.addAction("Add Channel")
        channel_toolbar.addAction("Remove Channel")
        # TODO link actions
        layout.addWidget(channel_toolbar)
        self._channel_list_widget = QListWidget(channel_panel)
        layout.addWidget(self._channel_list_widget)
        channel_panel.setLayout(layout)
        self._parent_widget.addWidget(channel_panel)

        transition_panel = QWidget(self._parent_widget)
        layout = QVBoxLayout()
        transition_toolbar = QToolBar(transition_panel)
        transition_toolbar.addAction("Add Transition")
        transition_toolbar.addAction("Link Events")
        transition_toolbar.addSeparator()
        transition_toolbar.addAction("Remove Transition")
        # TODO link actions
        layout.addWidget(transition_toolbar)
        self._transition_list_widget = QListWidget(transition_panel)
        self._transition_list_widget.currentRowChanged.connect(self._transition_selected)
        layout.addWidget(self._transition_list_widget)
        transition_panel.setLayout(layout)
        self._parent_widget.addWidget(transition_panel)

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
        self._parent_widget.setStretchFactor(2, 2)
        # TODO make remaining general purpose methods (parent_closed) from cue editor reusable
        # TODO relink bankset on every changed selected transition

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
        self._timeline_container.cue = new_transition.to_cue()
        self._selected_transition = new_transition

    def _deselect_transition(self):
        if self._selected_transition is None:
            return
        self._selected_transition.update_frames_from_cue(self._timeline_container.cue, self._model.channels)

    def _add_transition(self, t: Transition, is_new_transition: bool = True):
        if is_new_transition:
            self._model.transitions.append(t)
        li = AnnotatedListWidgetItem(self._transition_list_widget)
        li.setText(str(self._transition_list_widget.count()))  # TODO add human readable name index to model
        li.annotated_data = t
        self._transition_list_widget.addItem(li)
        if is_new_transition:
            self._transition_selected(t)

    def _add_channel(self, c: SequencerChannel, is_new_transition: bool = True):
        if is_new_transition:
            self._model.channels.append(c)
        li = AnnotatedListWidgetItem(self._channel_list_widget)
        li.setText(f"[{c.data_type.format_for_filters()}] {c.name}")
        li.annotated_data = c
        self._channel_list_widget.addItem(li)

    def _populate_data(self):
        for c in self._model.channels:
            self._add_channel(c, is_new_transition=False)
        if len(self._model.transitions) > 0:
            for t in self._model.transitions:
                self._add_transition(t, is_new_transition=False)
            self._transition_selected(self._model.transitions[-1])

    def _rec_pressed(self):
        pass  # TODO
