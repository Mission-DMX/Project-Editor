import os
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedLayout,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

import proto.Events_pb2
from model import Broadcaster, events
from model.events import EventSender, get_sender_by_id, mark_sender_persistent
from proto.Events_pb2 import event
from utility import resource_path
from view.action_setup_view._audio_setup_widget import AudioSetupWidget
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem, AnnotatedTableWidgetItem

if TYPE_CHECKING:
    from collections.abc import ItemsView

logger = getLogger(__name__)
_xtouch_gpio_icon = QIcon(resource_path(os.path.join("resources", "icons", "eventsource-gpio.svg")))
_plain_icon = QIcon(resource_path(os.path.join("resources", "icons", "eventsource-plain.svg")))
_keypad_icon = QIcon(resource_path(os.path.join("resources", "icons", "eventsource-keypad.svg")))
_midi_icon = QIcon(resource_path(os.path.join("resources", "icons", "eventsource-midi.svg")))
_midirtp_icon = QIcon(resource_path(os.path.join("resources", "icons", "eventsource-midirtp.svg")))
_rename_icon = QIcon(resource_path(os.path.join("resources", "icons", "rename.svg")))
_audio_icon = QIcon(resource_path(os.path.join("resources", "icons", "audio.svg")))

_event_type_string: dict[proto.Events_pb2.event_type, str] = {
    proto.Events_pb2.ONGOING_EVENT: "Ongoing",
    proto.Events_pb2.START: "Start",
    proto.Events_pb2.RELEASE: "End",
    proto.Events_pb2.SINGLE_TRIGGER: "Single",
}


class _SenderConfigurationWidget(QScrollArea):
    """Widget containing the configuration of the current selected event sender."""

    def __init__(self, parent: QWidget | None, b: Broadcaster) -> None:
        super().__init__(parent=parent)
        self._sender: events.EventSender | None = None
        layout = QFormLayout()
        self._name_label = QLabel(self)
        f = self._name_label.font()
        f.setPixelSize(16)
        self._name_label.setFont(f)
        layout.addWidget(self._name_label)
        self._index_label = QLabel(self)
        layout.addRow("Index on fish: ", self._index_label)
        self._type_label = QLabel(self)
        layout.addRow("Type: ", self._type_label)
        self._persistence_checkbox = QCheckBox(self)
        self._persistence_checkbox.setText("Sender Persistence")
        self._persistence_checkbox.checkStateChanged.connect(self._persistence_changed)
        layout.addWidget(self._persistence_checkbox)
        self._debug_enabled_checkbox = QCheckBox(self)
        self._debug_enabled_checkbox.setText("Enable Event logging")
        self._debug_enabled_checkbox.checkStateChanged.connect(self._debug_enabled_checked_changed)
        layout.addWidget(self._debug_enabled_checkbox)
        self._debug_include_ongoing_checkbox = QCheckBox(self)
        self._debug_include_ongoing_checkbox.setText("Include Ongoing Events")
        self._debug_include_ongoing_checkbox.checkStateChanged.connect(self._debug_include_ongoing_changed)
        layout.addWidget(self._debug_include_ongoing_checkbox)
        self._custom_conf_layout = QStackedLayout()
        custom_conf_widget = QWidget(self)
        self._no_custom_config_label = QLabel(custom_conf_widget)
        self._custom_conf_layout.addWidget(self._no_custom_config_label)
        self._audio_config_widget = AudioSetupWidget(custom_conf_widget)
        self._custom_conf_layout.addWidget(self._audio_config_widget)
        # TODO implement individual configuration widgets for remaining sender types
        custom_conf_widget.setLayout(self._custom_conf_layout)
        layout.addWidget(custom_conf_widget)
        self._apply_config_button = QPushButton(self)
        self._apply_config_button.setText("Update configuration now.")
        self._apply_config_button.clicked.connect(self._update_configuration)
        layout.addWidget(self._apply_config_button)
        self._rename_table = QTableWidget(self, rowCount=0, columnCount=4)
        self._rename_table.cellChanged.connect(self._rename_table_cell_changed)
        layout.addWidget(self._rename_table)
        # TODO add manual rename button
        self.setLayout(layout)
        self._own_rename_issued = False
        self._broadcaster = b
        self.sender = None
        self._update_widgets_on_new_sender(None)
        b.event_rename_action_occurred.connect(self._rename_event_occurred)

    @property
    def sender(self) -> events.EventSender | None:
        return self._sender

    @sender.setter
    def sender(self, new_sender: events.EventSender | None) -> None:
        if new_sender == self._sender:
            return
        self._sender = new_sender
        self._update_widgets_on_new_sender(new_sender)

    def _update_widgets_on_new_sender(self, new_sender: events.EventSender | None) -> None:
        if new_sender is not None:
            self._name_label.setText(new_sender.name)
            self._index_label.setText(str(new_sender.index_on_fish))
            self._type_label.setText(new_sender.type)
            self._persistence_checkbox.setChecked(new_sender.persistent)
            self._persistence_checkbox.setEnabled(True)
            self._debug_enabled_checkbox.setChecked(new_sender.debug_enabled)
            self._debug_enabled_checkbox.setEnabled(True)
            self._debug_include_ongoing_checkbox.setChecked(new_sender.debug_include_ongoing_events)
            self._debug_include_ongoing_checkbox.setEnabled(new_sender.debug_enabled)
            self._rename_table.setEnabled(True)
            self._update_table()
            if isinstance(new_sender, events.AudioExtractEventSender):
                self._custom_conf_layout.setCurrentWidget(self._audio_config_widget)
                self._audio_config_widget.update_from_sender(new_sender)
                self._apply_config_button.setEnabled(True)
            else:
                self._custom_conf_layout.setCurrentWidget(self._no_custom_config_label)
                self._apply_config_button.setEnabled(False)
        else:
            self._name_label.setText("")
            self._index_label.setText("")
            self._type_label.setText("")
            self._persistence_checkbox.setChecked(False)
            self._persistence_checkbox.setEnabled(False)
            self._debug_enabled_checkbox.setChecked(False)
            self._debug_enabled_checkbox.setEnabled(False)
            self._debug_include_ongoing_checkbox.setChecked(False)
            self._debug_include_ongoing_checkbox.setEnabled(False)
            self._rename_table.clear()
            self._rename_table.setRowCount(0)
            self._rename_table.setEnabled(False)
            self._apply_config_button.setEnabled(False)
            self._custom_conf_layout.setCurrentWidget(self._no_custom_config_label)

    def _update_table(self) -> None:
        self._rename_table.clear()
        rename_items: ItemsView[tuple[int, int, str], str] = self._sender.renamed_events.items()
        self._rename_table.setRowCount(len(rename_items))

        for i, k, v in enumerate(rename_items):
            name_item = AnnotatedTableWidgetItem(v)
            name_item.annotated_data = k
            ev_type_item = QTableWidgetItem(_event_type_string.get(k[0], k[0]))
            ev_type_item.setFlags(ev_type_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
            s_function_item = QTableWidgetItem(str(k[1]))
            s_function_item.setFlags(
                s_function_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable
            )
            args_item = QTableWidgetItem(k[2])
            args_item.setFlags(args_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
            self._rename_table.setItem(i, 0, name_item)
            self._rename_table.setItem(i, 1, ev_type_item)
            self._rename_table.setItem(i, 2, s_function_item)
            self._rename_table.setItem(i, 3, args_item)

    def _debug_enabled_checked_changed(self) -> None:
        if self._sender is not None:
            self._sender.debug_enabled = self._debug_enabled_checkbox.isChecked()
            self._debug_include_ongoing_checkbox.setEnabled(self._sender.debug_enabled)

    def _debug_include_ongoing_changed(self) -> None:
        if self._sender is not None:
            self._sender.debug_include_ongoing_events = self._debug_include_ongoing_checkbox.isChecked()

    def _persistence_changed(self) -> None:
        if self._sender is not None:
            self._sender.persistent = self._persistence_checkbox.isChecked()

    def _rename_table_cell_changed(self, row: int, column: int) -> None:
        if self._sender is None:
            return
        item = self._rename_table.item(row, column)
        if not isinstance(item, AnnotatedTableWidgetItem):
            return
        self._sender.renamed_events[item.annotated_data] = item.text()
        self._own_rename_issued = True
        self._broadcaster.event_rename_action_occurred.emit(self._sender.index_on_fish)

    def _rename_event_occurred(self, s_id: int) -> None:
        if not self._own_rename_issued:
            if self._sender is not None and self._sender.index_on_fish == s_id:
                self._update_table()
        else:
            self._own_rename_issued = False

    def _update_configuration(self):
        if self._sender is not None:
            self._sender.send_update(auto_commit=True, push_direct=True)


class _SourceListWidget(QWidget):
    """Content widget for ListWidgetItems of event senders"""

    def __init__(self, parent: QWidget, sender: events.EventSender) -> None:
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        text_layout = QVBoxLayout()
        self._icon_label = QLabel(self)
        self._icon_label.setMaximumWidth(66)
        self._icon_label.setMinimumWidth(64)
        if isinstance(sender, events.XtouchGPIOEventSender):
            self._icon_label.setPixmap(_xtouch_gpio_icon.pixmap(64, 64))
        if isinstance(sender, events.AudioExtractEventSender):
            self._icon_label.setPixmap(_audio_icon.pixmap(64, 64))
        else:
            self._icon_label.setPixmap(_plain_icon.pixmap(64, 64))
        layout.addWidget(self._icon_label)
        self._name_label = QLabel(self)
        self._name_label.setText(sender.name)
        text_layout.addWidget(self._name_label)
        self._id_label = QLabel(self)
        self._id_label.setText(f"Index: {sender.index_on_fish}")
        self._id_label.setEnabled(False)
        text_layout.addWidget(self._id_label)
        layout.addLayout(text_layout)
        self.setLayout(layout)


class _EventLogListWidget(QWidget):
    """Content widget for ListWidgetItems of logged events"""

    _STYLE_ID_TAG = """
    background-color: #B0B0B0;
    color: #FFFFFF;
    border-radius: 5px;
    padding: 3px;
    """

    _STYLE_TAG_REGULAR = """
    border-radius: 5px;
    padding: 3px;
    background-color: #B0B0B0;
    border: 2px solid #262626;
    color: #FFFFFF;
    """

    _STYLE_TAG_START = """
    border-radius: 5px;
    padding: 3px;
    background-color: #B0B0B0;
    border: 2px solid #262626;
    color: #00A000;
    """

    _STYLE_TAG_RELEASE = """
    border-radius: 5px;
    padding: 3px;
    background-color: #B0B0B0;
    border: 2px solid #262626;
    color: #FF0000;
    """

    def __init__(self, parent: QWidget, ev: event, b: Broadcaster) -> None:
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self._id_label = QLabel(str(ev.event_id), parent=self)
        self._id_label.setToolTip("Event ID")
        self._id_label.setStyleSheet(_EventLogListWidget._STYLE_ID_TAG)
        self._sender_label = QLabel(f"[{ev.sender_id}:{ev.sender_function}]", parent=self)
        self._sender_label.setToolTip("Event Sender and function")
        self._type_label = QLabel(_event_type_string.get(ev.type, ev.type), parent=self)
        if ev.type == proto.Events_pb2.START:
            self._type_label.setStyleSheet(_EventLogListWidget._STYLE_TAG_START)
        elif ev.type == proto.Events_pb2.RELEASE:
            self._type_label.setStyleSheet(_EventLogListWidget._STYLE_TAG_RELEASE)
        else:
            self._type_label.setStyleSheet(_EventLogListWidget._STYLE_TAG_REGULAR)
        self._type_label.setToolTip("Event Type")
        self._args_label = QLabel(", ".join([str(arg) for arg in ev.arguments]), parent=self)
        self._args_label.setToolTip("Event Arguments")
        self._add_rename_button = QPushButton(self)
        self._add_rename_button.setFixedWidth(32)
        self._add_rename_button.setIcon(_rename_icon)
        self._add_rename_button.clicked.connect(self._add_rename_entry)
        layout.addWidget(self._add_rename_button)
        self._name_label = QLabel(self)
        self._name_label.setVisible(False)
        layout.addWidget(self._name_label)
        intermediate_layout = QHBoxLayout()
        intermediate_layout.addWidget(self._id_label)
        intermediate_layout.addStretch()
        layout.addLayout(intermediate_layout)
        intermediate_layout = QHBoxLayout()
        intermediate_layout.addWidget(self._sender_label)
        intermediate_layout.addStretch()
        layout.addLayout(intermediate_layout)
        intermediate_layout = QHBoxLayout()
        intermediate_layout.addWidget(self._type_label)
        intermediate_layout.addStretch()
        layout.addLayout(intermediate_layout)
        intermediate_layout = QHBoxLayout()
        intermediate_layout.addWidget(self._args_label)
        intermediate_layout.addStretch()
        layout.addLayout(intermediate_layout)
        self.setLayout(layout)
        self._event = ev
        self._broadcaster = b
        self._broadcaster.event_rename_action_occurred.connect(self._rename_occurred)
        self._update_name_label()

    def _add_rename_entry(self) -> None:
        sender = get_sender_by_id(self._event.sender_id)
        if sender is None:
            return
        sender.renamed_events[self._get_event_tuple()] = "New Event"
        self._broadcaster.event_rename_action_occurred.emit(sender.index_on_fish)

    def _get_event_tuple(self) -> tuple[int, int, str]:
        return int(self._event.type), self._event.sender_function, "".join([chr(c) for c in self._event.arguments])

    def _rename_occurred(self, sid: int) -> None:
        if sid != self._event.sender_id:
            return
        self._update_name_label()

    def _update_name_label(self) -> None:
        sender = get_sender_by_id(self._event.sender_id)
        name = sender.renamed_events.get(self._get_event_tuple())
        if name is not None:
            self._add_rename_button.setVisible(False)
            self._add_rename_button.setEnabled(False)
            self._name_label.setVisible(True)
            self._name_label.setFixedWidth(32)
            self._name_label.setText(name)
            self._name_label.setToolTip(name)


class _SenderAddDialog(QDialog):
    """Dialog to configure new event senders."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Add Event Sender")
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._button_box.rejected.connect(self.close)
        self._button_box.accepted.connect(self._apply)
        layout = QFormLayout()
        self._name_tb = QLineEdit(self)
        self._name_tb.setPlaceholderText("Enter sender name here")
        layout.addRow("Name: ", self._name_tb)
        self._type_cb = QComboBox(self, editable=False)
        self._type_cb.addItems(
            [
                "fish.builtin.plain",
                "fish.builtin.midi",
                "fish.builtin.midirtp",
                "fish.builtin.xtouchgpio",
                "fish.builtin.gpio",
                "fish.builtin.audioextract",
                "fish.builtin.macrokeypad",
            ]
        )
        layout.addRow("Type: ", self._type_cb)
        layout.addWidget(self._button_box)
        self.setLayout(layout)

    def _apply(self) -> None:
        evs = EventSender(self._name_tb.text())
        evs.type = self._type_cb.currentText()
        mark_sender_persistent(evs.name)
        evs.send_update(auto_commit=True, push_direct=True)
        self.close()


class EventSetupWidget(QSplitter):

    """Widget containing the entire event sender configuration UI."""

    def __init__(self, parent: QWidget | None, b: Broadcaster):
        super().__init__(parent=parent)
        self._selection_panel = QWidget(self)
        layout = QVBoxLayout()
        self._selection_panel.setLayout(layout)
        self._button_pannel = QToolBar(self._selection_panel)
        self._button_pannel.addAction(QIcon.fromTheme("list-add"), "Add Sender", self._add_sender_pressed)
        self._button_pannel.addAction(QIcon.fromTheme("edit-clear"), "Clear Log", self._clear_log_pressed)
        layout.addWidget(self._button_pannel)
        self._sender_list = QListWidget(self._selection_panel)
        self._sender_list.setMinimumWidth(100)
        self._sender_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._sender_list.itemSelectionChanged.connect(self._sender_selected)
        layout.addWidget(self._sender_list)
        self.addWidget(self._selection_panel)
        self._update_sender_list()
        b.event_sender_model_updated.connect(self._update_sender_list)
        self._config_splitter = QSplitter(self)
        self._config_splitter.setMinimumWidth(100)
        self._config_splitter.setOrientation(Qt.Orientation.Vertical)
        self.addWidget(self._config_splitter)
        self._configuration_widget = _SenderConfigurationWidget(self._config_splitter, b)
        self._configuration_widget.setMinimumHeight(100)
        self._config_splitter.addWidget(self._configuration_widget)
        self._log_container = QWidget(self._config_splitter)
        log_layout = QVBoxLayout()
        self._log_container.setLayout(log_layout)
        label_layout = QHBoxLayout()
        label_layout.addSpacing(48)
        for label_str in ["Event ID", "Sender:Function", "Type", "Arguments"]:
            intermediate_layout = QHBoxLayout()
            intermediate_layout.addWidget(QLabel(label_str, parent=self._log_container))
            intermediate_layout.addStretch()
            label_layout.addLayout(intermediate_layout)
        log_layout.addLayout(label_layout)
        self._event_log = QListWidget(self._log_container)
        self._event_log.setMinimumHeight(100)
        log_layout.addWidget(self._event_log)
        self._config_splitter.addWidget(self._log_container)
        self.setStretchFactor(1, 2)
        self._config_splitter.setStretchFactor(0, 2)
        b.fish_event_received.connect(self._event_received)
        self._broadcaster = b
        self._dialog: QDialog | None = None

    def _update_sender_list(self) -> None:
        self._sender_list.clear()
        for sender in events.get_all_senders():
            item = AnnotatedListWidgetItem(self._sender_list)
            item_widget = _SourceListWidget(self._sender_list, sender)
            item.setSizeHint(item_widget.sizeHint())
            item.annotated_data = sender
            self._sender_list.addItem(item)
            self._sender_list.setItemWidget(item, item_widget)

    def _sender_selected(self) -> None:
        item_list = self._sender_list.selectedItems()
        if len(item_list) == 0:
            return
        item = item_list[0]
        if not isinstance(item, AnnotatedListWidgetItem):
            raise ValueError("Expected out item implementation")
        self._configuration_widget.sender = item.annotated_data

    def _add_sender_pressed(self) -> None:
        self._dialog = _SenderAddDialog(self)
        self._dialog.open()

    def _event_received(self, e: event) -> None:
        if e.type == proto.Events_pb2.ONGOING_EVENT and not get_sender_by_id(e.sender_id).debug_include_ongoing_events:
            return
        item = AnnotatedListWidgetItem(self._event_log)
        w = _EventLogListWidget(self._event_log, e, self._broadcaster)
        item.setSizeHint(w.sizeHint())
        item.annotated_data = e
        self._event_log.addItem(item)
        self._event_log.setItemWidget(item, w)

    def _clear_log_pressed(self) -> None:
        self._event_log.clear()
