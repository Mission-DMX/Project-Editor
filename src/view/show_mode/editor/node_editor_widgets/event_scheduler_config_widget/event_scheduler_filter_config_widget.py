"""Filter configuration widget for event scheduler filter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSpinBox,
    QWidget,
)

from model.events import TriggerType
from utility import to_int
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.event_scheduler_config_widget.event_list_item_widget import (
    EventListItemWidget,
)
from view.show_mode.editor.node_editor_widgets.event_scheduler_config_widget.trigger_matrix_editor import (
    TriggerMatrixEditor,
)
from view.show_mode.editor.node_editor_widgets.sequencer_editor.event_selection_dialog import EventSelectionDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from collections.abc import Callable

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
        btn_layout = QHBoxLayout()
        self._add_event_btn = QPushButton("Add Event")
        self._add_event_btn.clicked.connect(self._add_event_clicked)
        btn_layout.addWidget(self._add_event_btn)
        self._remove_event_btn = QPushButton("Remove Event")
        self._remove_event_btn.clicked.connect(self._remove_event_clicked)
        btn_layout.addWidget(self._remove_event_btn)
        btn_layout.addStretch()
        self._add_step_btn = QPushButton("+")
        self._add_step_btn.clicked.connect(self._add_step)
        btn_layout.addWidget(self._add_step_btn)
        self._remove_step_btn = QPushButton("-")
        self._remove_step_btn.clicked.connect(self._remove_step)
        btn_layout.addWidget(self._remove_step_btn)
        layout.addRow("Change number of steps", btn_layout)
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
        self._sync_trigger_group.setLayout(sync_trigger_layout)
        layout.addWidget(self._sync_trigger_group)
        self._widget.setLayout(layout)
        self._open_event_dialogs: set[EventSelectionDialog] = set()

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {
            "event_data": ";".join(self._encode_event_data()),
            "event_names": ";".join(self._matrix_editor.event_names),
        }

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._matrix_editor.clear()
        self._event_list.clear()
        event_entries = conf.get("event_data", "").split(";")
        event_descriptions: list[str] = []
        decoded_event_entries: list[tuple[int, int, TriggerType, list[int]]] = []
        for event_entry in event_entries:
            if len(event_entry) < 1:
                continue
            args = event_entry.split(",")
            if len(args) < 3:
                logger.warning("Skipping malformed event entry %r.", event_entry)
                continue
            event_type_value = to_int(args[2], -1)
            try:
                event_type = TriggerType(event_type_value)
            except ValueError:
                logger.warning("Skipping event entry %r with unknown trigger type %r.", event_entry, args[2])
                continue
            sender = to_int(args[0], 0)
            sender_function = to_int(args[1], 0)
            ev_arguments: list[int] = [to_int(s, 0) for s in args[3:] if len(s) > 0]
            decoded_event_entries.append((sender, sender_function, event_type, ev_arguments))
            event_descriptions.append(event_entry)
        event_names = conf.get("event_names", "").split(";")
        if len(decoded_event_entries) == 0:
            return
        if len(event_names) > len(decoded_event_entries):
            logger.warning("Dropping %d surplus event name entries.", len(event_names) - len(decoded_event_entries))
            del event_names[len(decoded_event_entries) :]
        while len(event_names) < len(decoded_event_entries):
            event_names.append("No Name")
        for event_description, decoded_representation, name in zip(
            event_descriptions, decoded_event_entries, event_names, strict=False
        ):
            self._matrix_editor.add_event(event_description, name)
            sender, sender_function, event_type, ev_arguments = decoded_representation
            self._append_event_item(name, sender, sender_function, event_type, ev_arguments)

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        number_of_steps = to_int(parameters.get("length", "0"), 0)
        self._matrix_editor.number_of_steps = number_of_steps
        self._matrix_editor.active_event_data = parameters.get("update_triggers", "")
        default_step = to_int(parameters.get("step", "0"), 0)
        self._matrix_editor.current_step = default_step
        self._default_step_tb.setValue(default_step)
        self._default_step_tb.setMaximum(max(number_of_steps - 1, 0))
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)
        sync_target_parts = parameters.get("synchronization_target", "0,0").split(",")
        if len(sync_target_parts) != 2:
            logger.warning(
                "Malformed synchronization target %r, falling back to 0,0.", parameters.get("synchronization_target")
            )
            sync_target_parts = ["0", "0"]
        self._sync_trigger_sender_tb.setValue(to_int(sync_target_parts[0], 0))
        self._sync_trigger_function_tb.setValue(to_int(sync_target_parts[1], 0))

    @override
    def _get_parameters(self) -> dict[str, str]:
        """Return the initial filter parameters."""
        return {
            "length": str(self._matrix_editor.number_of_steps),
            "update_triggers": self._matrix_editor.active_event_data,
            "step": str(self._default_step_tb.value()),
            "synchronization_target": (
                f"{self._sync_trigger_sender_tb.value()},{self._sync_trigger_function_tb.value()}"
            ),
        }

    @override
    def parent_opened(self) -> None:
        pass  # nothing to do here

    @staticmethod
    def _encode_event(sender_id: int, sender_function: int, event_type: TriggerType, arguments: list[int]) -> str:
        """Serialize an event description, omitting the argument section if the event has no arguments."""
        event_section = f"{sender_id},{sender_function},{event_type.value}"
        if arguments:
            event_section += "," + ",".join(str(argument) for argument in arguments)
        return event_section

    def _encode_event_data(self) -> list[str]:
        event_str_list = []
        for i in range(self._event_list.count()):
            item = self._event_list.item(i)
            if not isinstance(item, AnnotatedListWidgetItem):
                logger.error("Expected AnnotatedListWidgetItem.")
                continue
            item_data = item.annotated_data
            if not isinstance(item_data, tuple):
                logger.error("Expected AnnotatedListWidgetItem to be of correct type.")
                continue
            sender_id, sender_function, event_type, arguments = item_data
            event_str_list.append(self._encode_event(sender_id, sender_function, event_type, arguments))
        return event_str_list

    def _append_event_item(
        self,
        name: str,
        sender_id: int,
        sender_function: int,
        event_type: TriggerType,
        arguments: list[int],
    ) -> None:
        """Add a fully populated list entry backed by an EventListItemWidget."""
        list_item = AnnotatedListWidgetItem(self._event_list)
        list_item.annotated_data = (sender_id, sender_function, event_type, arguments)
        item_widget = EventListItemWidget(name, sender_id, sender_function, event_type, arguments, self._event_list)
        item_widget.name_changed.connect(lambda text, w=item_widget: self._on_event_name_changed(w, text))
        item_widget.trigger_type_changed.connect(
            lambda new_type, w=item_widget: self._on_event_trigger_type_changed(w, new_type)
        )
        list_item.setSizeHint(item_widget.sizeHint())
        self._event_list.addItem(list_item)
        self._event_list.setItemWidget(list_item, item_widget)

    def _row_for_widget(self, widget: QWidget) -> int:
        for row in range(self._event_list.count()):
            item = self._event_list.item(row)
            if self._event_list.itemWidget(item) is widget:
                return row
        return -1

    def _on_event_name_changed(self, widget: EventListItemWidget, new_name: str) -> None:
        row = self._row_for_widget(widget)
        if row < 0:
            return
        event_names = list(self._matrix_editor.event_names)
        if not 0 <= row < len(event_names):
            logger.warning("Renamed list entry %d has no matching event in the matrix editor.", row)
            return
        if event_names[row] == new_name:
            return
        event_names[row] = new_name
        self._matrix_editor.event_names = event_names

    def _on_event_trigger_type_changed(self, widget: EventListItemWidget, new_type: TriggerType) -> None:
        row = self._row_for_widget(widget)
        if row < 0:
            return
        item = self._event_list.item(row)
        if not isinstance(item, AnnotatedListWidgetItem):
            return
        data = item.annotated_data
        if not isinstance(data, tuple):
            return
        sender_id, sender_function, _, arguments = data
        item.annotated_data = (sender_id, sender_function, new_type, arguments)
        self._matrix_editor.update_event(row, self._encode_event(sender_id, sender_function, new_type, arguments))

    def _select_trigger_clicked(self, _: bool) -> None:
        self._open_event_selection_dialog(self._event_selected)

    def _open_event_selection_dialog(self, on_accepted: Callable[[EventSelectionDialog], None]) -> None:
        """Open an event selection dialog and dispatch its result to the given callback.

        The dialog is tracked until it finishes (accepted or rejected), so it is neither garbage-collected while
        visible nor confused with another open dialog: the accepted callback always receives the dialog it was
        registered for, even if more than one dialog is open at the same time.
        """
        dialog = EventSelectionDialog()
        dialog.accepted.connect(lambda: on_accepted(dialog))
        dialog.finished.connect(lambda _result: self._event_dialog_finished(dialog))
        self._open_event_dialogs.add(dialog)
        dialog.show()

    def _event_dialog_finished(self, dialog: EventSelectionDialog) -> None:
        """Forget an event selection dialog that has finished (accepted or rejected)."""
        self._open_event_dialogs.discard(dialog)
        dialog.deleteLater()

    def _event_selected(self, dialog: EventSelectionDialog) -> None:
        """Apply the synchronization trigger selected in the given dialog."""
        sender, function, _ = dialog.selected_event
        self._sync_trigger_sender_tb.setValue(sender)
        self._sync_trigger_function_tb.setValue(function)

    def _add_step(self, _: bool) -> None:
        self._matrix_editor.number_of_steps += 1
        self._default_step_tb.setMaximum(max(self._matrix_editor.number_of_steps - 1, 0))
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)

    def _remove_step(self, _: bool) -> None:
        self._matrix_editor.number_of_steps -= 1
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)
        self._default_step_tb.setMaximum(max(self._matrix_editor.number_of_steps - 1, 0))

    def _add_event_clicked(self, _: bool) -> None:
        self._open_event_selection_dialog(self._event_added)

    def _remove_event_clicked(self, _: bool) -> None:
        """Remove the currently selected event from the event list and the trigger matrix."""
        selected_row = self._event_list.currentRow()
        if not 0 <= selected_row < self._event_list.count():
            return
        item = self._event_list.item(selected_row)
        if item is not None:
            item_widget = self._event_list.itemWidget(item)
            if item_widget is not None:
                item_widget.deleteLater()
        taken_item = self._event_list.takeItem(selected_row)
        del taken_item  # dropping the reference deletes the item and removes its row from the list
        self._matrix_editor.remove_event(selected_row)

    def _event_added(self, dialog: EventSelectionDialog) -> None:
        """Add the event selected in the given dialog to the scheduler configuration."""
        sender, sender_function, arg_string = dialog.selected_event
        initial_name = f"New event [{sender}:{sender_function}]"
        ev_arguments = [ord(c) for c in arg_string]
        event_type = TriggerType.SINGLE_TRIGGER
        event_description = self._encode_event(sender, sender_function, event_type, ev_arguments)
        self._matrix_editor.add_event(event_description, initial_name)
        self._append_event_item(initial_name, sender, sender_function, event_type, ev_arguments)
