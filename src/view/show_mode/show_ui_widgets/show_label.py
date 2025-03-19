# TODO add text ui widget
from PySide6.QtWidgets import QWidget, QLabel, QTextEdit
from markdown import markdown

from model import UIWidget

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from model import UIPage


class ShowLabelUIWidget(UIWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self._widget: QLabel | None = None
        self._edit_widget : QTextEdit | None = None

    def generate_update_content(self) -> list[tuple[str, str]]:
        # This is merely a label. We do not need to update anything.
        return []

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._widget is None:
            self._construct_widget()
        return self._widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if self._widget is None:
            self._construct_widget()
        return self._widget

    def _construct_widget(self):
        w = QLabel()
        w.setWordWrap(True)
        w.setText(markdown(self.configuration.get("text") or ""))
        w.setMinimumWidth(100)
        w.setMinimumHeight(10)
        self._widget = w

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = ShowLabelUIWidget(new_parent, self.configuration.copy())
        super().copy_base(w)
        return w

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        if self._edit_widget is not None:
            return self._edit_widget
        w = QTextEdit(parent)
        self._edit_widget = w
        w.setAcceptRichText(True)
        w.setText(self.configuration.get("text") or "")
        w.setMinimumHeight(100)
        w.setMinimumWidth(200)
        w.textChanged.connect(self._editor_text_changed)
        return w

    def _editor_text_changed(self):
        new_text = self._edit_widget.toMarkdown()
        self.configuration["text"] = new_text
        if self._widget is not None:
            self._widget.setText(markdown(new_text))
