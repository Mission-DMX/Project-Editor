from PySide6.QtGui import QStandardItemModel, QStandardItem, Qt
from PySide6.QtWidgets import QDialog, QWidget, QLabel, QFormLayout, QListView, QDialogButtonBox


class SelectionDialog(QDialog):
    def __init__(self, title: str, message: str, items: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        form = QFormLayout(self)
        form.addRow(QLabel(message))
        self.listView = QListView(self)
        form.addRow(self.listView)
        model = QStandardItemModel(self.listView)
        self.setWindowTitle(title)
        for item_name in items:
            item = QStandardItem(item_name)
            item.setCheckable(True)
            model.appendRow(item)
        self.listView.setModel(model)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                      Qt.Orientation.Horizontal, self)
        form.addRow(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    @property
    def selected_items(self) -> list[str]:
        selected = []
        model = self.listView.model()
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
