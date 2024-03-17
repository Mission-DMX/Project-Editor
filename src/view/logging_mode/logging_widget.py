# coding=utf-8
"""widget for logging_mode"""
import json
import logging
from typing import List

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCompleter

from model.broadcaster import Broadcaster

from .logging_item_widget import LoggingItemWidget
from .search import Operation, Search


class LoggingWidget(QtWidgets.QTabWidget):
    """widget for logging_mode"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._broadcaster = Broadcaster()
        self._broadcaster.log_message.connect(self.new_log_message)

        searchbar = QtWidgets.QLineEdit()
        searchbar.textChanged.connect(self.update_display)
        completer = QCompleter(["level", "message", "timestamp", "logger", "module", "function", "line", "thread_name"])
        searchbar.setCompleter(completer)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["key", "value"])
        self._tree.setColumnWidth(0, 150)
        self._tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tree.setLayout(QtWidgets.QVBoxLayout())

        self._log_items: List[LoggingItemWidget] = []

        container_layout = QtWidgets.QVBoxLayout()
        container_layout.addWidget(searchbar)
        container_layout.addWidget(self._tree)

        self.setLayout(container_layout)

        logging.info("start DMXGui")

    def new_log_message(self, message: str) -> None:
        """handle incoming log messages"""
        new_log_item: LoggingItemWidget = LoggingItemWidget(self._tree, json.loads(message))
        self._log_items.append(new_log_item)
        self._tree.addTopLevelItem(new_log_item)

    def update_display(self, text: str) -> None:
        """update display for searching items"""
        search: list[Search] = []
        ands: [str] = text.split("&")
        for item in ands:
            part = item.split(":")
            if len(part) == 2:
                search.append(Search((part[0], part[1]), Operation.AND))
        for widget in self._log_items:
            widget.search(search)
