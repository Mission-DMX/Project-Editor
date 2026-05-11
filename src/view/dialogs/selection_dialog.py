"""Contains a selection dialog."""

from collections.abc import Callable
from typing import override

from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QLabel, QListView, QWidget


class SelectionDialog(QDialog):
    """A dialog allowing the user to select items in a list."""

    def __init__(self, title: str, message: str, items: list[str], parent: QWidget | None = None,
                 multi_selection_allowed: bool = True, selected_callback: Callable | None = None) -> None:
        """Initialize the dialog.

        Args:
            title: The window title of the dialog.
            message: The displayed message or help text of the dialog.
            items: The list of items to present in the dialog.
            parent: The parent Qt widget of the dialog.
            multi_selection_allowed: Whether the dialog should allow selection of multiple items.
            selected_callback: Optional callback function that will be called when selection is completed.

        """
        super().__init__(parent)
        form = QFormLayout(self)
        form.addRow(QLabel(message))
        self.list_view = QListView(self)
        form.addRow(self.list_view)
        model = QStandardItemModel(self.list_view)
        self.setWindowTitle(title)
        for item_name in items:
            item = QStandardItem(item_name)
            # TODO use radio buttons if multi_selection_allowed == False
            item.setCheckable(True)
            model.appendRow(item)
        self.list_view.setModel(model)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Horizontal, self
        )
        form.addRow(button_box)
        if not multi_selection_allowed:
            self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.setModal(True)
        self._selection_callable = selected_callback

    @property
    def selected_items(self) -> list[str]:
        """Get the items the user selected."""
        selected = []
        model = self.list_view.model()
        i = 0
        while model.item(i):
            if model.item(i).checkState() == Qt.CheckState.Checked:
                selected.append(model.item(i).text())
            i += 1
        return selected

    @override
    def accept(self) -> None:
        super().accept()
        if self._selection_callable is not None:
            self._selection_callable(self)
        self.close()

    @override
    def reject(self) -> None:
        super().reject()
        self.close()
