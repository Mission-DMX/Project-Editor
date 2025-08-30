"""Contains SequenceTriggerInsertionDialog."""

from collections.abc import Callable
from typing import override

from PySide6.QtWidgets import QComboBox, QWidget

from model import BoardConfiguration
from model.filter import FilterTypeEnumeration
from model.filter_data.sequencer.sequencer_filter_model import SequencerFilterModel
from model.macro import Macro
from view.action_setup_view._command_insertion_dialog import _CommandInsertionDialog
from view.action_setup_view._command_insertion_dialog import escape_argument as esc


class SequenceTriggerInsertionDialog(_CommandInsertionDialog):
    """Dialog to insert triggers for sequences."""

    def __init__(self, parent: QWidget, macro: Macro, show: BoardConfiguration, update_callable: Callable) -> None:
        """Initialize the dialog.

        Args:
            parent: The parent widget.
            macro: The macro model.
            show: The show model.
            update_callable: Method to be called after user confirmation.

        """
        super().__init__(parent, macro, [FilterTypeEnumeration.VFILTER_SEQUENCER], show, update_callable)
        self._sequence_selection_cb = QComboBox(self)
        self._sequence_selection_cb.setEnabled(False)
        self._sequence_selection_cb.setEditable(False)
        self._custom_layout.addWidget(self._sequence_selection_cb)
        self._custom_layout.setCurrentIndex(0)

    @override
    def on_filter_selected(self) -> None:
        self._sequence_selection_cb.setEnabled(True)
        self._sequence_selection_cb.clear()
        filter_model = SequencerFilterModel()
        filter_model.load_configuration(self._filter_selection.selected_filter.filter_configurations)
        for i, t in enumerate(filter_model.transitions):
            self._sequence_selection_cb.addItem(t.name or str(i), t.trigger_event)

    @override
    def get_command(self) -> str:
        data = self._sequence_selection_cb.currentData()
        return (
            f"event send -i {esc(data[0])} --function {esc(data[1])} --args {esc(data[2])}  # trigger "
            f"transition {self._sequence_selection_cb.currentText()}"
        )
