"""Contains a selection dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QLabel, QListView, QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QStyledItemDelegate


class SelectionDialog(QDialog):
    """A dialog allowing the user to select items in a list.

    Due to its nature it is well-suited for larger data collections.

    """

    def __init__(self, title: str, message: str, items: list[str], parent: QWidget | None = None,
                 multi_selection_allowed: bool = True, selected_callback: Callable | None = None,
                 widget_delegate: QStyledItemDelegate | None = None) -> None:
        """Initialize the dialog.

        It is possible to specify the item widget using widget_class.

        Args:
            title: The window title of the dialog.
            message: The displayed message or help text of the dialog.
            items: The list of items to present in the dialog.
            parent: The parent Qt widget of the dialog.
            multi_selection_allowed: Whether the dialog should allow selection of multiple items.
            selected_callback: Optional callback function that will be called when selection is completed.
            widget_delegate: A QStyledItemDelegate that can be used to style items.

        """
        super().__init__(parent)
        self._multi_selection_allowed = multi_selection_allowed
        form = QFormLayout(self)
        form.addRow(QLabel(message))
        self.list_view = QListView(self)
        if widget_delegate is not None:
            self.list_view.setItemDelegate(widget_delegate)
            self.list_view.setUniformItemSizes(False)
        form.addRow(self.list_view)
        model = QStandardItemModel(self.list_view)
        self.setWindowTitle(title)
        for item_name in items:
            item = QStandardItem(item_name)
            item.setCheckable(multi_selection_allowed)
            item.setEditable(False)
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
        model = self.list_view.model()
        if self._multi_selection_allowed:
            selected = []
            i = 0
            while model.item(i):
                if model.item(i).checkState() == Qt.CheckState.Checked:
                    selected.append(model.item(i).text())
                i += 1
            return selected
        return [model.item(index.row()).text() for index in self.list_view.selectedIndexes()]

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
