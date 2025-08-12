"""Contains a selection dialog."""
from typing import override

from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QListView, QWidget


class SelectionDialog(QDialog):
    """A dialog allowing the user to select items in a list."""

    def __init__(self, title: str, message: str, items: list[str], parent: QWidget | None = None) -> None:
        """Initialize the dialog.

        :param title: The window title of the dialog.
        :param message: The displayed message or help text of the dialog.
        :param items: The list of items to present in the dialog.
        :param parent: The parent Qt widget of the dialog.
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
            item.setCheckable(True)
            model.appendRow(item)
        self.list_view.setModel(model)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                      Qt.Orientation.Horizontal, self)
        form.addRow(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.setModal(True)

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
        self.close()

    @override
    def reject(self) -> None:
        super().reject()
        self.close()
