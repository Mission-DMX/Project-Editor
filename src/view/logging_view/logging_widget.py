# coding=utf-8
"""widget for logging_view"""
import json
import logging
from typing import List

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCompleter

from model.broadcaster import Broadcaster

from .logging_item_widget import LoggingItemWidget
from .search import Operation, Search


class LoggingWidget(QtWidgets.QTabWidget):
    """widget for logging_view"""
    _loging_level_changed: QtCore.Signal = QtCore.Signal(tuple)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        select_bar = QtWidgets.QMenuBar()
        level_menu = QtWidgets.QMenu("Level")
        self._levels: dict = {
            "DEBUG": QAction("Debug", level_menu, checkable=True, checked=False,
                             changed=(lambda: self._loging_level_changed.emit(
                                 ("DEBUG", self._levels["DEBUG"].isChecked())))),
            "INFO": QAction("Info", level_menu, checkable=True, checked=False,
                            changed=(
                                lambda: self._loging_level_changed.emit(("INFO", self._levels["INFO"].isChecked())))),
            "WARNING": QAction("WARNING", level_menu, checkable=True, checked=True,
                               changed=(
                                   lambda: self._loging_level_changed.emit(
                                       ("WARNING", self._levels["WARNING"].isChecked())))),
            "ERROR": QAction("Error", level_menu, checkable=True, checked=True,
                             changed=(
                                 lambda: self._loging_level_changed.emit(
                                     ("ERROR", self._levels["ERROR"].isChecked())))),
            "CRITICAL": QAction("Critical", level_menu, checkable=True, checked=True,
                                changed=(
                                    lambda: self._loging_level_changed.emit(
                                        ("CRITICAL", self._levels["CRITICAL"].isChecked()))))
        }
        level_menu.addAction(QAction("all", level_menu, triggered=(lambda: self.all_log_levels(True))))
        for value in self._levels.values():
            level_menu.addAction(value)
        level_menu.addAction(QAction("none", level_menu, triggered=(lambda: self.all_log_levels(False))))
        select_bar.addMenu(level_menu)

        self._broadcaster = Broadcaster()
        self._broadcaster.log_message.connect(self.new_log_message)

        searchbar = QtWidgets.QLineEdit()
        searchbar.textChanged.connect(self.update_display)
        completer = QCompleter(["message", "timestamp", "logger", "module", "function", "line", "thread_name"])
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
        container_layout.addWidget(select_bar)
        container_layout.addWidget(searchbar)
        container_layout.addWidget(self._tree)

        self.setLayout(container_layout)

        logging.info("start DMXGui")

    def all_log_levels(self, value: bool):
        """set all log levels"""
        for level in self._levels.values():
            level.setChecked(value)

    def new_log_message(self, message: str) -> None:
        """handle incoming log messages"""
        message_dict = json.loads(message)
        level = message_dict["level"]
        new_log_item: LoggingItemWidget = LoggingItemWidget(self._tree, message_dict, level,
                                                            self._levels[level].isChecked(), self._loging_level_changed)
        self._log_items.append(new_log_item)
        self._tree.addTopLevelItem(new_log_item)

    def update_display(self, text: str) -> None:
        """update display for searching items"""
        search: list[Search] = []
        ands: [str] = text.split("&")
        for item in ands:
            part = item.split(":")
            if len(part) == 2:
                search.append(Search((part[0], part[1]), Operation.IS))
        for widget in self._log_items:
            widget.search(search)
