from typing import Any

from PySide6.QtWidgets import QListWidgetItem, QTableWidgetItem, QTreeWidgetItem


class AnnotatedTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, parent):
        super().__init__(parent)
        self._annotated_data = None

    @property
    def annotated_data(self):
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data) -> None:
        self._annotated_data = new_data


class AnnotatedListWidgetItem(QListWidgetItem):

    def __init__(self, parent):
        super().__init__(parent)
        self._annotated_data = None

    @property
    def annotated_data(self):
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data) -> None:
        self._annotated_data = new_data


class AnnotatedTableWidgetItem(QTableWidgetItem):
    def __init__(self, other: Any):
        super().__init__(other)
        self._annotated_data: Any = None

    @property
    def annotated_data(self):
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data) -> None:
        self._annotated_data = new_data
