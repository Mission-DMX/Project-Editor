# coding=utf-8
"""widget for logging_mode"""

import logging

from PySide6 import QtWidgets


class LoggingHandler(logging.Handler):
    """logging_mode Handler"""

    def __init__(self, parent) -> None:
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record: logging.LogRecord) -> None:
        """emit logging message"""
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class LoggingWidget(QtWidgets.QTabWidget):
    """widget for logging_mode"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        log_text_box = LoggingHandler(self)
        log_text_box.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_text_box)

        layout = QtWidgets.QVBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(log_text_box.widget)
        self.setLayout(layout)

        logging.info("start DMXGui")
