from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget

from model import UIWidget


class SequencerControlUIWidget(UIWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None

    def generate_update_content(self) -> list[tuple[str, str]]:
        return []

    def _construct_widget(self, parent: QWidget | None) -> QWidget:
        w = QWidget(parent=parent)
        w.setMinimumWidth(300)
        w.setMinimumHeight(100)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Current Active Sequences:"))
        list_widget = QListWidget()
        # TODO listen on updates from filter and update widget with it
        layout.addWidget(list_widget)
        w.setLayout(layout)
        return w

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        self._player_widget = self._construct_widget(parent)
        return self._player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        self._configuration_widget = self._construct_widget(parent)
        return self._configuration_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        new_widget = SequencerControlUIWidget(new_parent, self.configuration.copy())
        self.copy_base(new_widget)
        return new_widget

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        # TODO should we provide configuration options?
        return QWidget(parent=parent)
