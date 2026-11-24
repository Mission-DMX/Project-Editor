"""Contains Qt item widgets that can carry additional data."""

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QTableWidgetItem, QTreeWidget, QTreeWidgetItem


class AnnotatedTreeWidgetItem(QTreeWidgetItem):
    """Tree widget item that can carry additional data."""

    def __init__(self, parent: QTreeWidget | QTreeWidgetItem) -> None:
        """Initialize using the provided parent."""
        super().__init__(parent)
        self._annotated_data: object | None = None

    @property
    def annotated_data(self) -> object | None:
        """The additional data of the item."""
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: object) -> None:
        self._annotated_data = new_data


class AnnotatedListWidgetItem(QListWidgetItem):
    """List widget item that can carry additional data."""

    def __init__(self, parent: QListWidget) -> None:
        """Initialize using the provided parent."""
        super().__init__(parent)
        self._annotated_data: object | None = None

    @property
    def annotated_data(self) -> object | None:
        """The additional data of the item."""
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: object) -> None:
        self._annotated_data = new_data


class AnnotatedTableWidgetItem(QTableWidgetItem):
    """Table widget item that can carry additional data."""

    def __init__(self, other: str) -> None:
        """Initialize using the provided text."""
        super().__init__(other)
        self._annotated_data: tuple | None = None

    @property
    def annotated_data(self) -> tuple | None:
        """The additional data of the item."""
        return self._annotated_data

    @annotated_data.setter
    def annotated_data(self, new_data: tuple) -> None:
        self._annotated_data = new_data
