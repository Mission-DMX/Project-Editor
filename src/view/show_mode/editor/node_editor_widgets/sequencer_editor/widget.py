from PySide6.QtWidgets import QListWidget, QSplitter, QToolBar, QVBoxLayout, QWidget

from model import Filter
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (ExternalChannelDefinition,
                                                                                      PreviewEditWidget)


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
        layout.addWidget(self._transition_list_widget)
        transition_panel.setLayout(layout)
        self._parent_widget.addWidget(transition_panel)

        timeline_panel = QWidget(self._parent_widget)
        layout = QVBoxLayout()
        timeline_toolbar = QToolBar(timeline_panel)
        # TODO port timeline tool bar from cue editor to preview editor
        timeline_toolbar.addWidget(self._zoom_label)
        layout.addWidget(timeline_toolbar)
        layout.addWidget(self._timeline_container)
        timeline_panel.setLayout(layout)
        self._parent_widget.addWidget(timeline_panel)
        self._parent_widget.setStretchFactor(2, 2)
        # TODO make general purpose methods (zoom + zoom_panel, bankset linking, timeline toolbar, parent_closed)
        #  from cue editor reusable

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
        pass  # TODO

    def _populate_data(self):
        pass  # TODO

    def _rec_pressed(self):
        pass  # TODO
