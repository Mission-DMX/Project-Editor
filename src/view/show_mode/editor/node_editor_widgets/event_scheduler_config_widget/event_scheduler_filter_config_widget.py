"""Filter configuration widget for event scheduler filter."""

from __future__ import annotations

from logging import getLogger
from typing import override

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
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.event_scheduler_config_widget.event_list_item_widget import (
    EventListItemWidget,
)
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
        btn_layout = QHBoxLayout()
        self._add_event_btn = QPushButton("Add Event")
        self._add_event_btn.clicked.connect(self._add_event_clicked)
        btn_layout.addWidget(self._add_event_btn)
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
        self._dialog: EventSelectionDialog | None = None

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {
            "event_data": ";".join(self._encode_event_data()),
            "event_names": ";".join(self._matrix_editor.event_names)
        }

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._matrix_editor.clear()
        self._event_list.clear()
        event_entries = conf.get("event_data", "").split(";")
        decoded_event_entries: list[tuple[int, int, TriggerType, list[int]]] = []
        for event_entry in event_entries:
            if len(event_entry) < 1:
                continue
            args = event_entry.split(",")
            sender: int = int(args.pop(0))
            sender_function: int = int(args.pop(0))
            event_type: TriggerType = TriggerType(int(args.pop(0)))
            ev_arguments: list[int] = [int(s) for s in args if len(s) > 0] if len(args) > 0 else []
            decoded_event_entries.append((sender, sender_function, event_type, ev_arguments))
        event_names = conf.get("event_names", "").split(";")
        if len(decoded_event_entries) == 0:
            return
        while len(event_names) < len(decoded_event_entries):
            event_names.append("No Name")
        try:
            for event_description, decoded_representation, name in (
                    zip(event_entries, decoded_event_entries, event_names, strict=True)):
                self._matrix_editor.add_event(event_description, name)
                sender, sender_function, event_type, ev_arguments = decoded_representation
                self._append_event_item(name, sender, sender_function, event_type, ev_arguments)
        except ValueError as e:
            logger.error("Unable to unpack configuration: %s. Event descriptions: %s, event_names: %s",
                         str(e), str(event_entries), str(event_names))

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        number_of_steps = int(parameters.get("length", "0"))
        self._matrix_editor.number_of_steps = number_of_steps
        self._matrix_editor.active_event_data = parameters.get("update_triggers", "")
        default_step = int(parameters.get("step", "0"))
        self._matrix_editor.current_step = default_step
        self._default_step_tb.setValue(default_step)
        self._default_step_tb.setMaximum(max(number_of_steps - 1, 0))
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)
        sync_sender_id, sync_sender_function = parameters.get("synchronization_target", "0,0").split(",")
        self._sync_trigger_sender_tb.setValue(int(sync_sender_id))
        self._sync_trigger_function_tb.setValue(int(sync_sender_function))

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {
            "length" : str(self._matrix_editor.number_of_steps),
            "update_triggers": self._matrix_editor.active_event_data,
            "step": str(self._default_step_tb.value()),
            "synchronization_target": f"{self._sync_trigger_sender_tb.value()},{self._sync_trigger_function_tb.value()}"
        }

    @override
    def parent_opened(self) -> None:
        pass  # nothing to do here

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
            event_str_list.append(
                f"{sender_id},{sender_function},{event_type.value},{",".join(str(a) for a in arguments)}"
            )
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
        item_widget = EventListItemWidget(
            name, sender_id, sender_function, event_type, arguments, self._event_list
        )
        item_widget.name_changed.connect(
            lambda text, w=item_widget: self._on_event_name_changed(w, text)
        )
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
        self._default_step_tb.setMaximum(max(self._matrix_editor.number_of_steps - 1, 0))
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)

    def _remove_step(self, _: bool) -> None:
        self._matrix_editor.number_of_steps -= 1
        self._remove_step_btn.setEnabled(self._matrix_editor.number_of_steps > 0)
        self._default_step_tb.setMaximum(max(self._matrix_editor.number_of_steps - 1, 0))

    def _add_event_clicked(self, _: bool) -> None:
        self._dialog = EventSelectionDialog()
        self._dialog.accepted.connect(self._event_added_final)
        self._dialog.show()

    def _event_added_final(self) -> None:
        sender, sender_function, args = self._dialog.selected_event
        initial_name = f"New event [{sender}:{sender_function}]"
        args = [ord(c) for c in args]
        event_type = TriggerType.SINGLE_TRIGGER
        self._matrix_editor.add_event(f"{sender},{sender_function},{event_type.value}{
            ',' + ','.join(str(a) for a in args) if len(args) > 0 else ''}", initial_name)
        self._append_event_item(initial_name, sender, sender_function, event_type, args)
