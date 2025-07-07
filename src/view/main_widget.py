"""baseline for all Views """

from PySide6 import QtWidgets


class MainWidget(QtWidgets.QMainWindow):
    """main View Styling"""

    def __init__(self, widget: QtWidgets, parent):
        super().__init__(parent=parent)
        self._widget: QtWidgets = widget
        self.setCentralWidget(self._widget)
        self._toolbar = self.addToolBar("widget")
        try:
            for tool in self._widget.toolbar:
                self._toolbar.addAction(tool)
        except AttributeError:
            self.removeToolBar(self._toolbar)
