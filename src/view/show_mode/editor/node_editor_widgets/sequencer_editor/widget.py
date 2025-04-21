from PySide6.QtWidgets import QWidget

from model import Filter
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (ExternalChannelDefinition,
                                                                                      PreviewEditWidget)


class SequencerEditor(PreviewEditWidget):

    def __init__(self, parent: QWidget = None, f: Filter | None = None):
        super().__init__()
        self._parent_widget = QWidget(parent=parent)
        self._model = SequencerFilterModel()
        # TODO add widgets
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
