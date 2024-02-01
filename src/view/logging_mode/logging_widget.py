# coding=utf-8
"""widget for logging_mode"""
import json
import logging
from typing import List

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from model.broadcaster import Broadcaster
from .logging_item_widget import LoggingItemWidget


class LoggingWidget(QtWidgets.QTabWidget):
    """widget for logging_mode"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self._broadcaster.log_message.connect(self.new_log_message)

        searchbar = QtWidgets.QLineEdit()
        searchbar.textChanged.connect(self.update_display)

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(True)
        self._scroll.setLayout(QtWidgets.QVBoxLayout())

        self._log_items: List[LoggingItemWidget] = []

        container_layout = QtWidgets.QVBoxLayout()
        container_layout.addWidget(searchbar)
        container_layout.addWidget(self._scroll)

        self.setLayout(container_layout)

        logging.info("start DMXGui")

    def new_log_message(self, message: str) -> None:
        """ handle incoming log messages """
        massage_content: dict = json.loads(message)
        new_log_item: LoggingItemWidget = LoggingItemWidget(self._scroll, massage_content["message"])
        self._log_items.append(new_log_item)
        self._scroll.layout().addWidget(new_log_item)

    def update_display(self, text: str) -> None:
        """update display for searching items"""
        for widget in self._log_items:
            if text.lower() in widget.content.lower():
                widget.show()
            else:
                widget.hide()
