"""Definition of a single logging item in logging Widget"""
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QTreeWidgetItem

from ..dialogs.fish_exception_dialog import FishExceptionsDialog, error_dict
from .search import Operation, Search


class LoggingItemWidget(QtWidgets.QTreeWidgetItem):
    """Widget of a single logging item"""

    def __init__(self, parent, message: dict, level: str, visible: bool, visible_change: QtCore.Signal(str, bool)):
        super().__init__(parent)
        visible_change.connect(self._level_visible_change)
        self._content: dict = message
        self.setText(0, level)
        self._level = level
        self._possible_visible = visible
        self.setHidden(not visible)
        self.setText(1, message["message"].split("\n")[0])
        for key, value in message.items():
            self.addChild(QTreeWidgetItem([key, str(value)]))

        message_text = message["message"]
        for key in error_dict:
            if key in message_text:
                tmp = message_text.split("Logs:\n")[1].split("Reason: ")
                log: str = tmp[0]
                tmp = tmp[1].split("Possible causes: ")
                reason: str = tmp[0]
                causes: str = tmp[1] if len(tmp) > 1 else "No more info"
                ex = FishExceptionsDialog(log, reason, causes)
                ex.exec()
                break

    def _level_visible_change(self, level: tuple[str, bool]) -> None:
        """change the visibility of a logging item by level"""
        if self._level == level[0]:
            self._possible_visible = level[1]
            if not self._possible_visible:
                self.setHidden(True)
            else:
                self.setHidden(False)  # TODO eigentlich search

    def search(self, search: list[Search]) -> None:
        """hide all not feasible items"""
        visible = self._possible_visible
        if visible:
            for entry in search:
                match entry.operation:
                    case Operation.IS:
                        if not (
                            entry.items[0] in self._content and entry.items[1] in self._content[entry.items[0]]
                        ):
                            visible = False
        self.setHidden(not visible)
