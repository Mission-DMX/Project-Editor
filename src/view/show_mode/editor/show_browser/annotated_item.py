from PySide6.QtWidgets import QListWidget, QListWidgetItem, QTableWidgetItem, QTreeWidget, QTreeWidgetItem

from model.scene import FilterPage


class AnnotatedTreeWidgetItem(QTreeWidgetItem):

    def __init__(self, parent: QTreeWidget) -> None:
        super().__init__(parent)
        self._annotated_data: FilterPage | None = None

    @property
    def annotated_data(self) -> FilterPage | None:
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: FilterPage) -> None:
        self._annotated_data = new_data


class AnnotatedListWidgetItem(QListWidgetItem):

    def __init__(self, parent: QListWidget) -> None:
        super().__init__(parent)
        self._annotated_data: object | None = None

    @property
    def annotated_data(self) -> object | None:
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: object) -> None:
        self._annotated_data = new_data


class AnnotatedTableWidgetItem(QTableWidgetItem):
    def __init__(self, other: str) -> None:
        super().__init__(other)
        self._annotated_data: tuple[int, int, str] | None = None

    @property
    def annotated_data(self) -> tuple[int, int, str] | None:
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: tuple[int, int, str]) -> None:
        self._annotated_data = new_data
