from PySide6.QtWidgets import QComboBox, QWidget

from model import BoardConfiguration
from model.filter import FilterTypeEnumeration
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from model.macro import Macro
from view.action_setup_view._command_insertion_dialog import _CommandInsertionDialog


class SequenceTriggerInsertionDialog(_CommandInsertionDialog):
    def __init__(self, parent: QWidget, macro: Macro, show: BoardConfiguration, update_callable: callable):
        super().__init__(
            parent, macro,[FilterTypeEnumeration.VFILTER_SEQUENCER],
            show, update_callable
        )
        self._sequence_selection_cb = QComboBox(self)
        self._sequence_selection_cb.setEnabled(False)
        self._sequence_selection_cb.setEditable(False)
        self.custom_layout.addWidget(self._sequence_selection_cb)
        self.custom_layout.setCurrentIndex(0)

    def on_filter_selected(self):
        self._sequence_selection_cb.setEnabled(True)
        self._sequence_selection_cb.clear()
        filter_model = SequencerFilterModel()
        filter_model.load_configuration(self._filter_selection.selected_filter.filter_configurations)
        i = 0
        for t in filter_model.transitions:
            self._sequence_selection_cb.addItem(t.name or str(i), t._trigger_event)
            i += 1

    def get_command(self) -> str:
        data = self._sequence_selection_cb.currentData()
        return f"event send -i {data[0]} --function {data[1]} --args {data[2]}  # trigger transition {self._sequence_selection_cb.currentText()}"
