"""Show UI Widget containing arbitrary text."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from markdown import markdown
from PySide6.QtWidgets import QDialog, QLabel, QTextEdit, QWidget

from model import UIWidget

if TYPE_CHECKING:
    from model import UIPage


class ShowLabelUIWidget(UIWidget):
    """Widget to display user defined rich text (markdown)."""

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize the label widget.

        :param parent: The parent widget page.
        :param configuration: The initial configuration of the sequencer.
        """
        super().__init__(parent, configuration)
        self._player_widget: QLabel | None = None
        self._conf_widget: QLabel | None = None
        self._edit_widget: QTextEdit | None = None

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        # This is merely a label. We do not need to update anything.
        return []

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        self._player_widget = self._construct_widget(parent)
        return self._player_widget

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if self._conf_widget is not None:
            self._conf_widget.deleteLater()
        self._conf_widget = self._construct_widget(parent)
        return self._conf_widget

    def _construct_widget(self, parent: QWidget) -> QWidget:
        w = QLabel(parent)
        w.setWordWrap(True)
        w.setText(markdown(self.configuration.get("text") or ""))
        w.setMinimumWidth(100)
        w.setMinimumHeight(10)
        return w

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = ShowLabelUIWidget(new_parent, self.configuration.copy())
        super().copy_base(w)
        return w

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
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

    def _editor_text_changed(self) -> None:
        new_text = self._edit_widget.toMarkdown()
        self.configuration["text"] = new_text
        text_as_html = markdown(new_text)
        if self._conf_widget is not None:
            self._conf_widget.setText(text_as_html)
            self._conf_widget.setMinimumWidth(max(self._conf_widget.fontMetrics().horizontalAdvance(new_text),
                                                  self._conf_widget.minimumWidth()))
        if self._player_widget is not None:
            self._player_widget.setText(text_as_html)
            self._player_widget.setMinimumWidth(max(self._player_widget.fontMetrics().horizontalAdvance(new_text),
                                                    self._player_widget.minimumWidth()))
