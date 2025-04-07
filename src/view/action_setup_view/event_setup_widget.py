from logging import getLogger

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QCheckBox, QFormLayout, QHBoxLayout, QLabel, QListWidget, QScrollArea, QSplitter,
                               QToolBar, QVBoxLayout, QWidget)

import proto.Events_pb2
from model import Broadcaster, events
from model.events import get_sender_by_id
from proto.Events_pb2 import event
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__file__)
_xtouch_gpio_icon = QIcon("resources/icons/eventsource-gpio.svg")
_plain_icon = QIcon("resources/icons/eventsource-plain.svg")
_keypad_icon = QIcon("resources/icons/eventsource-keypad.svg")
_midi_icon = QIcon("resources/icons/eventsource-midi.svg")
_midirtp_icon = QIcon("resources/icons/eventsource-midirtp.svg")


class _SenderConfigurationWidget(QScrollArea):
    def __init__(self, parent: QWidget | None):
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
        self._debug_enabled_checkbox = QCheckBox(self)
        self._debug_enabled_checkbox.setText("Enable Event logging")
        self._debug_enabled_checkbox.checkStateChanged.connect(self._debug_enabled_checked_changed)
        layout.addWidget(self._debug_enabled_checkbox)
        self._debug_include_ongoing_checkbox = QCheckBox(self)
        self._debug_include_ongoing_checkbox.setText("Include Ongoing Events")
        self._debug_include_ongoing_checkbox.checkStateChanged.connect(self._debug_include_ongoing_changed)
        layout.addWidget(self._debug_include_ongoing_checkbox)
        # TODO implement individual configuration widgets for event sender types
        self.setLayout(layout)
        self.sender = None

    @property
    def sender(self) -> events.EventSender | None:
        return self._sender

    @sender.setter
    def sender(self, new_sender: events.EventSender | None):
        self._sender = new_sender
        if new_sender is not None:
            self._name_label.setText(new_sender.name)
            self._index_label.setText(str(new_sender.index_on_fish))
            self._type_label.setText(new_sender.type)
            self._debug_enabled_checkbox.setChecked(new_sender.debug_enabled)
            self._debug_enabled_checkbox.setEnabled(True)
            self._debug_include_ongoing_checkbox.setChecked(new_sender.debug_include_ongoing_events)
            self._debug_include_ongoing_checkbox.setEnabled(new_sender.debug_enabled)
        else:
            self._name_label.setText("")
            self._index_label.setText("")
            self._type_label.setText("")
            self._debug_enabled_checkbox.setChecked(False)
            self._debug_enabled_checkbox.setEnabled(False)
            self._debug_include_ongoing_checkbox.setEnabled(False)

    def _debug_enabled_checked_changed(self, *args, **kwargs):
        if self._sender is not None:
            self._sender.debug_enabled = self._debug_enabled_checkbox.isChecked()
            self._debug_include_ongoing_checkbox.setEnabled(self._sender.debug_enabled)

    def _debug_include_ongoing_changed(self):
        if self._sender is not None:
            self._sender.debug_include_ongoing_events = self._debug_include_ongoing_checkbox.isChecked()


class _SourceListWidget(QWidget):

    def __init__(self, parent: QWidget, sender: events.EventSender):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        text_layout = QVBoxLayout()
        self._icon_label = QLabel(self)
        self._icon_label.setMaximumWidth(66)
        self._icon_label.setMinimumWidth(64)
        if isinstance(sender, events.XtouchGPIOEventSender):
            self._icon_label.setPixmap(_xtouch_gpio_icon.pixmap(64, 64))
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
        # TODO add persistence indicator
        self.setLayout(layout)


def _type_to_string(t):
    """Get the string representation of an event type"""
    if t == proto.Events_pb2.ONGOING_EVENT:
        return "Ongoing"
    elif t == proto.Events_pb2.START:
        return "Start"
    elif t == proto.Events_pb2.RELEASE:
        return "End"
    elif t == proto.Events_pb2.SINGLE_TRIGGER:
        return "Single"
    else:
        return str(t)


class _EventLogListWidget(QWidget):

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

    def __init__(self, parent: QWidget, ev: event):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self._id_label = QLabel(str(ev.event_id), parent=self)
        self._id_label.setToolTip("Event ID")
        self._id_label.setStyleSheet(_EventLogListWidget._STYLE_ID_TAG)
        self._sender_label = QLabel("[{}:{}]".format(ev.sender_id, ev.sender_function), parent=self)
        self._sender_label.setToolTip("Event Sender and function")
        self._type_label = QLabel(_type_to_string(ev.type), parent=self)
        if ev.type == proto.Events_pb2.START:
            self._type_label.setStyleSheet(_EventLogListWidget._STYLE_TAG_START)
        elif ev.type == proto.Events_pb2.RELEASE:
            self._type_label.setStyleSheet(_EventLogListWidget._STYLE_TAG_RELEASE)
        else:
            self._type_label.setStyleSheet(_EventLogListWidget._STYLE_TAG_REGULAR)
        self._type_label.setToolTip("Event Type")
        self._args_label = QLabel(", ".join([str(arg) for arg in ev.arguments]), parent=self)
        self._args_label.setToolTip("Event Arguments")
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


class EventSetupWidget(QSplitter):

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
        self._configuration_widget = _SenderConfigurationWidget(self._config_splitter)
        self._configuration_widget.setMinimumHeight(100)
        self._config_splitter.addWidget(self._configuration_widget)
        self._log_container = QWidget(self._config_splitter)
        log_layout = QVBoxLayout()
        self._log_container.setLayout(log_layout)
        label_layout = QHBoxLayout()
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

    def _update_sender_list(self):
        self._sender_list.clear()
        for sender in events.get_all_senders():
            item = AnnotatedListWidgetItem(self._sender_list)
            item_widget = _SourceListWidget(self._sender_list, sender)
            item.setSizeHint(item_widget.sizeHint())
            item.annotated_data = sender
            self._sender_list.addItem(item)
            self._sender_list.setItemWidget(item, item_widget)

    def _sender_selected(self):
        item_list = self._sender_list.selectedItems()
        if len(item_list) == 0:
            return
        item = item_list[0]
        if not isinstance(item, AnnotatedListWidgetItem):
            raise ValueError("Expected out item implementation")
        self._configuration_widget.sender = item.annotated_data

    def _add_sender_pressed(self):
        pass  # TODO

    def _event_received(self, e: event):
        if e.type == proto.Events_pb2.ONGOING_EVENT:
            if not get_sender_by_id(e.sender_id).debug_include_ongoing_events:
                return
        item = AnnotatedListWidgetItem(self._event_log)
        w = _EventLogListWidget(self._event_log, e)
        item.setSizeHint(w.sizeHint())
        item.annotated_data = e
        self._event_log.addItem(item)
        self._event_log.setItemWidget(item, w)

    def _clear_log_pressed(self):
        self._event_log.clear()
