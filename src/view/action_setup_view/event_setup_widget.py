from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QScrollArea, QSplitter, QToolBar, QVBoxLayout, QWidget

from model import Broadcaster, events
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem


class _SenderConfigurationWidget(QScrollArea):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        # TODO implement


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
        # TODO implement repopulation
        for sender in events.get_all_senders():
            item = AnnotatedListWidgetItem(self._sender_list)
            item.setText(f"[{sender.index_on_fish}] {sender.name}")
            item.annotated_data = sender
            self._sender_list.addItem(item)
            # TODO set better item based on https://stackoverflow.com/questions/25187444/pyqt-qlistwidget-custom-items

    def _sender_selected(self):
        pass  # TODO

    def _add_sender_pressed(self):
        pass  # TODO
