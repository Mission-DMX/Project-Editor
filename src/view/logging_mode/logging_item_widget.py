# coding=utf-8
"""Definition of a single logging item in logging Widget"""
from PySide6 import QtWidgets
from PySide6.QtWidgets import QTreeWidgetItem

from .search import Operation, Search


class LoggingItemWidget(QtWidgets.QTreeWidgetItem):
    """Widget of a single logging item"""

    def __init__(self, parent, message: dict):
        super().__init__(parent)
        self._content: dict = message
        self.setText(0, message["level"])
        self.setText(1, message["message"].split("\n")[0])
        for key, value in message.items():
            self.addChild(QTreeWidgetItem([key, value]))

    def search(self, search: list[Search]) -> None:
        """hide all not feasible items"""
        visible = True
        for entry in search:
            match entry.operation:
                case Operation.AND:
                    if not (entry.items[0] in self._content.keys() and entry.items[1] in self._content[entry.items[0]]):
                        visible = False

        if visible:
            self.setHidden(False)
        else:
            self.setHidden(True)
