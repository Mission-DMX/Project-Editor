# coding=utf-8
"""widget for logging_mode"""
import json
import logging

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

        self._searchbar = QtWidgets.QLineEdit()

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setWidgetResizable(True)
        self._scroll.setLayout(QtWidgets.QVBoxLayout())

        container_layout = QtWidgets.QVBoxLayout()
        container_layout.addWidget(self._searchbar)
        container_layout.addWidget(self._scroll)

        self.setLayout(container_layout)

        logging.info("start DMXGui")

    def new_log_message(self, message: str):
        """ handle incoming log messages """
        massage_content: dict = json.loads(message)
        self._scroll.layout().addWidget(LoggingItemWidget(self._scroll, massage_content["message"]))
