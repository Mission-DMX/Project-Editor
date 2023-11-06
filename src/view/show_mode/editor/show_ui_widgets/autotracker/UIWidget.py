from PySide6.QtWidgets import QWidget

from model import UIWidget, UIPage


class AutoTrackerUIWidget(UIWidget):
    def generate_update_content(self) -> list[tuple[str, str]]:
        pass

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        pass

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        pass

    def copy(self, new_parent: UIPage) -> UIWidget:
        pass

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        pass
