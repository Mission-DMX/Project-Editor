from typing import override

from PySide6.QtWidgets import QDialog, QWidget

from model import UIPage, UIWidget


class ColorDirectorShowUIWidget(UIWidget):
    """Handles show UI widget interface for color director."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Initializes ColorDirectorShowUIWidget."""
        super().__init__(parent_page, configuration)

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        pass  # TODO

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        pass  # TODO

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        pass  # TODO

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        pass  # TODO

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        pass  # TODO
