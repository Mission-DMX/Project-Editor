from typing import override

from PySide6.QtWidgets import QDialog, QWidget

from model import UIPage, UIWidget
from view.show_mode.show_ui_widgets.colordirector._controller_widget import ControllerWidget


class ColorDirectorShowUIWidget(UIWidget):
    """Handles show UI widget interface for color director."""

    def __init__(self, parent_page: UIPage, configuration: dict[str, str] | None = None) -> None:
        """Initializes ColorDirectorShowUIWidget."""
        super().__init__(parent_page, configuration)

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        return []  # TODO

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        return ControllerWidget(self.parent.scene.get_filter_by_id(self.filter_ids[0]), parent)

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return ControllerWidget(self.parent.scene.get_filter_by_id(self.filter_ids[0]), parent)

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        pass  # TODO

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        pass  # TODO
