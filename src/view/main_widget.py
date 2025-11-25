"""baseline for all Views"""

from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget


class MainWidget(QtWidgets.QMainWindow):
    """main View Styling"""

    def __init__(self, widget: QtWidgets.QWidget, parent: QWidget = None) -> None:
        super().__init__(parent=parent)
        self._widget: QtWidgets.QWidget = widget
        self.setCentralWidget(self._widget)
