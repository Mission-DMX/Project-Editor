# coding=utf-8
"""widget for logging_mode"""
import json
import logging

from PySide6 import QtWidgets

from model.broadcaster import Broadcaster


class LoggingWidget(QtWidgets.QTabWidget):
    """widget for logging_mode"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._broadcaster = Broadcaster()

        self._widget = QtWidgets.QPlainTextEdit(parent)
        self._widget.setReadOnly(True)
        self._broadcaster.log_message.connect(self.new_log_message)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._widget)
        self.setLayout(layout)

        logging.info("start DMXGui")

    def new_log_message(self, massage: str):
        """ handle incoming log messages """
        massage_content: dict = json.loads(massage)

        self._widget.appendPlainText(massage_content["level"])
