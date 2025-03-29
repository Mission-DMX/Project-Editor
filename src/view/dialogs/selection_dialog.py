# coding=utf-8
from PySide6.QtGui import QStandardItem, QStandardItemModel, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QListView, QWidget


class SelectionDialog(QDialog):
    def __init__(self, title: str, message: str, items: list[str], parent: QWidget | None = None):
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

    @property
    def selected_items(self) -> list[str]:
        selected = []
        model = self.list_view.model()
        i = 0
        while model.item(i):
            if model.item(i).checkState() == Qt.CheckState.Checked:
                selected.append(model.item(i).text())
            i += 1
        return selected

    def accept(self):
        super().accept()
        self.close()

    def reject(self):
        super().reject()
        self.close()
