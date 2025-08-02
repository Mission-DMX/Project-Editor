from __future__ import annotations

import datetime
import os
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QFontDatabase, QFontMetrics
from PySide6.QtWidgets import QDialog, QLabel, QWidget
from tzlocal import get_localzone

from model import UIWidget
from utility import resource_path

if TYPE_CHECKING:
    from model import UIPage

_clock_font_id = QFontDatabase.addApplicationFont(
    resource_path(os.path.join("resources", "fonts", "roboto-mono-latin-700-normal.ttf")),
)
_font_families = QFontDatabase.applicationFontFamilies(_clock_font_id)


def _configure_label(w: QLabel) -> QLabel:
    f = QFont(_font_families[0], 45)
    fm = QFontMetrics(f)
    w.setFont(f)
    w.setMinimumWidth(fm.horizontalAdvance("00:00:00"))
    return w


class ClockUIWidget(UIWidget):
    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        super().__init__(parent, configuration)
        self._widget: QLabel | None = None
        self._timer: QTimer | None = None

    @override
    def generate_update_content(self) -> list[tuple[str, str]]:
        return []

    @override
    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._widget is not None:
            self._widget.deleteLater()
        self._construct_widget(parent)
        return self._widget

    @override
    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return _configure_label(QLabel("HH:MM:SS"))

    def _construct_widget(self, parent: QWidget | None) -> None:
        self._widget = _configure_label(QLabel(parent))
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_label)
        self._timer.start()
        self._update_label()

    def _update_label(self) -> None:
        ct = datetime.datetime.now(tz=get_localzone()).time()
        text = f"{ct.hour:02}:{ct.minute:02}:{ct.second:02}"
        self._widget.setText(text)

    @override
    def copy(self, new_parent: UIPage) -> UIWidget:
        w = ClockUIWidget(new_parent, self.configuration.copy())
        self.copy_base(w)
        return w

    @override
    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        return QLabel("No configuration for clock yet.")
