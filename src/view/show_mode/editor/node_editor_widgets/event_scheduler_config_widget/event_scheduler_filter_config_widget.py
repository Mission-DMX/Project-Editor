"""Filter configuration widget for event scheduler filter."""

from __future__ import annotations

from logging import getLogger
from typing import override

from PySide6.QtWidgets import QButtonGroup, QFormLayout, QGroupBox, QListWidget, QPushButton, QSpinBox, QWidget

from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.event_scheduler_config_widget.trigger_matrix_editor import (
    TriggerMatrixEditor,
)
from view.show_mode.editor.node_editor_widgets.sequencer_editor.event_selection_dialog import EventSelectionDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__name__)

class EventSchedulerSettingsWidget(NodeEditorFilterConfigWidget):
    """A widget to configure the event scheduler filter.

    Configuration options are:
     * default Trigger Event
     * output event data
     * default number of steps
     * default trigger data

    """

    def __init__(self) -> None:
        """Initialize the widget manager."""
        super().__init__()
        self._widget = QWidget()
        layout = QFormLayout()
        self._event_list = QListWidget()
        layout.addRow("Events", self._event_list)
        self._default_step_tb = QSpinBox()
        layout.addRow("Default step position", self._default_step_tb)
        self._add_or_remove_steps_btngroup = QButtonGroup()
        self._add_step_btn = QPushButton("+")
        self._add_step_btn.clicked.connect(self._add_step)
        self._add_or_remove_steps_btngroup.addButton(self._add_step_btn)
        self._remove_step_btn = QPushButton("-")
        self._remove_step_btn.clicked.connect(self._remove_step)
        self._add_or_remove_steps_btngroup.addButton(self._remove_step_btn)
        layout.addRow("Change number of steps", self._add_or_remove_steps_btngroup)
        self._matrix_editor = TriggerMatrixEditor(self._widget)
        layout.addWidget(self._matrix_editor)
        self._sync_trigger_group = QGroupBox("Synchronization Trigger", self._widget)
        sync_trigger_layout = QFormLayout()
        self._sync_trigger_sender_tb = QSpinBox()
        sync_trigger_layout.addRow("Sender ID", self._sync_trigger_sender_tb)
        self._sync_trigger_function_tb = QSpinBox()
        sync_trigger_layout.addRow("Function", self._sync_trigger_function_tb)
        self._sync_trigger_selection_btn = QPushButton("Select Trigger")
        self._sync_trigger_selection_btn.clicked.connect(self._select_trigger_clicked)
        sync_trigger_layout.addRow("", self._sync_trigger_selection_btn)
        layout.addWidget(self._sync_trigger_group)
        self._widget.setLayout(layout)
        self._dialog: EventSelectionDialog | None = None

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {
            "event_data": ";".join(self._encode_event_data()),
            "event_names": ";".join(self._matrix_editor.event_names)
        }

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        pass  # TODO

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        self._matrix_editor.number_of_steps = int(parameters["length"])
        self._matrix_editor.event_data = parameters["update_triggers"]
        default_step = int(parameters["step"])
        self._matrix_editor.current_step = default_step
        self._default_step_tb.setValue(default_step)
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {
            "length" : str(self._matrix_editor.number_of_steps),
            "update_triggers": self._matrix_editor.event_data,
            "step": str(self._default_step_tb.value()),
            "synchronization_target": f"{self._sync_trigger_sender_tb.value()},{self._sync_trigger_function_tb.value()}"
        }

    @override
    def parent_opened(self) -> None:
        pass  # TODO

    def _encode_event_data(self) -> list[str]:
        event_str_list = []
        for i in range(self._event_list.count()):
            item = self._event_list.item(i)
            if not isinstance(item, AnnotatedListWidgetItem):
                logger.error("Expected AnnotatedListWidgetItem.")
                continue
            sender_id, sender_function, event_type, arguments = item.annotated_data
            # FIXME implement event type encoding if required
            event_str_list.append(f"{sender_id},{sender_function},{event_type},{",".join(arguments)}")
        return event_str_list

    def _select_trigger_clicked(self, _: bool) -> None:
        self._dialog = EventSelectionDialog()
        self._dialog.accepted.connect(self._event_selected_callback)
        self._dialog.show()

    def _event_selected_callback(self) -> None:
        sender, function, _ = self._dialog.selected_event
        self._sync_trigger_sender_tb.setValue(sender)
        self._sync_trigger_function_tb.setValue(function)

    def _add_step(self, _: bool) -> None:
        self._matrix_editor.number_of_steps += 1

    def _remove_step(self, _: bool) -> None:
        self._matrix_editor.number_of_steps -= 1
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)
