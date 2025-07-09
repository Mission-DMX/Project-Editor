from typing import Any

from PySide6.QtWidgets import QListWidgetItem, QTableWidgetItem, QTreeWidgetItem, QListWidget, QTreeWidget

from model.events import EventSender
from model.scene import FilterPage


class AnnotatedTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, parent: QTreeWidget):
        super().__init__(parent)
        self._annotated_data: FilterPage | None = None

    @property
    def annotated_data(self) -> FilterPage | None:
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: FilterPage) -> None:
        self._annotated_data = new_data


class AnnotatedListWidgetItem(QListWidgetItem):

    def __init__(self, parent: QListWidget):
        super().__init__(parent)
        self._annotated_data: EventSender | None = None

    @property
    def annotated_data(self) -> EventSender | None:
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: EventSender) -> None:
        self._annotated_data = new_data


class AnnotatedTableWidgetItem(QTableWidgetItem):
    def __init__(self, other: Any):
        super().__init__(other)
        self._annotated_data: tuple[int, int, str] | None = None

    @property
    def annotated_data(self) -> tuple[int, int, str] | None:
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: tuple[int, int, str]) -> None:
        self._annotated_data = new_data
