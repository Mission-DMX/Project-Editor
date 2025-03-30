from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QScrollArea, QSplitter, QWidget

from model import Broadcaster


class _SenderConfigurationWidget(QScrollArea):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        # TODO implement


class EventSetupWidget(QSplitter):

    def __init__(self, parent: QWidget | None, b: Broadcaster):
        super().__init__(parent=parent)
        self._sender_list = QListWidget(self)
        self._sender_list.setMinimumWidth(100)
        self._sender_list.itemSelectionChanged.connect(self._sender_selected)
        self.addWidget(self._sender_list)
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

    def _sender_selected(self):
        pass  # TODO
