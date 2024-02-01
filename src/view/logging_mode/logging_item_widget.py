# coding=utf-8
"""Definition of a single logging item in logging Widget"""
from PySide6 import QtWidgets


class LoggingItemWidget(QtWidgets.QPlainTextEdit):
    """Widget of a single logging item"""

    def __init__(self, parent, message: str):
        super().__init__(parent)
        self.appendPlainText(message)
