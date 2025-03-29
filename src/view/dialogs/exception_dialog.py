# coding=utf-8
"""Dialogs to display exceptions"""
from PySide6.QtWidgets import QDialog, QFormLayout, QLabel


class ExceptionsDialog(QDialog):
    """Dialog to display generic exception"""
    _open_dialogs: list[QDialog] = []

    def __init__(self, exception: Exception):
        super().__init__()
        self.setWindowTitle("Error")
        layout = QFormLayout(self)
        error_msg = QLabel(str(exception), self)
        layout.addRow("Error", error_msg)
        self.setLayout(layout)

    def open(self):
        """Opens dialog and automatically keeps it open"""
        self._open_dialogs.append(self)
        self.finished.connect(lambda: self._open_dialogs.remove(self))
        super().open()
