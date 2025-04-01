from logging import getLogger

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QScrollArea, QSplitter, QToolBar, QVBoxLayout, QWidget

from model import Broadcaster, events
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
        # TODO implement


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
        self.setLayout(layout)


class EventSetupWidget(QSplitter):

    def __init__(self, parent: QWidget | None, b: Broadcaster):
        super().__init__(parent=parent)
        self._selection_panel = QWidget(self)
        layout = QVBoxLayout()
        self._selection_panel.setLayout(layout)
        self._button_pannel = QToolBar(self._selection_panel)
        self._button_pannel.addAction(QIcon.fromTheme("list-add"), "Add Sender", self._add_sender_pressed)
        layout.addWidget(self._button_pannel)
        self._sender_list = QListWidget(self._selection_panel)
        self._sender_list.setMinimumWidth(100)
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
        self._event_log = QListWidget(self._config_splitter)
        self._event_log.setMinimumHeight(100)
        self._config_splitter.addWidget(self._event_log)
        self.setStretchFactor(1, 2)
        self._config_splitter.setStretchFactor(0, 2)

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
        pass  # TODO

    def _add_sender_pressed(self):
        pass  # TODO
