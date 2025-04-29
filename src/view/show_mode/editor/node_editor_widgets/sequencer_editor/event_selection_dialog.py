from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QSpinBox, QWidget

if TYPE_CHECKING:
    from model import BoardConfiguration


class EventSelectionDialog(QDialog):
    def __init__(self, show: "BoardConfiguration", parent: QWidget | None = None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Select Event")
        self.selected_event: tuple[int, int, str] = (0, 0, "")
        layout = QFormLayout()
        # TODO add tree view to select stored combination
        # TODO fill combinations from show
        self._sender_tb = QSpinBox(self)
        self._sender_tb.valueChanged.connect(self._sender_value_changed)
        self._sender_tb.setMinimum(0)
        layout.addRow("Sender", self._sender_tb)
        self._function_tb = QSpinBox(self)
        self._function_tb.valueChanged.connect(self._function_value_changed)
        self._function_tb.setMinimum(0)
        layout.addRow("Function", self._function_tb)
        self._argument_tb = QLineEdit(self)
        self._argument_tb.setInputMask("9999999")
        self._argument_tb.textChanged.connect(self._arguments_changed)
        layout.addRow("Arguments", self._argument_tb)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                      Qt.Orientation.Horizontal, self)
        layout.addRow(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.setLayout(layout)

    def accept(self):
        super().accept()
        self.close()

    def reject(self):
        super().reject()
        self.close()

    def _sender_value_changed(self):
        self.selected_event = (self._sender_tb.value(), self.selected_event[1], self.selected_event[2])

    def _function_value_changed(self):
        self.selected_event = (self.selected_event[0], self._function_tb.value(), self.selected_event[2])

    def _arguments_changed(self):
        self.selected_event = (self.selected_event[0], self.selected_event[1], self._argument_tb.text())
