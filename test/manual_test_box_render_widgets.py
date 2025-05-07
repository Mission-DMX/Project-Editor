from PySide6 import QtWidgets
from PySide6.QtWidgets import QMainWindow

from view.utility_widgets.box_grid_renderer import BoxGridRenderer

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setDesktopSettingsAware(True)
    window = QMainWindow()

    widget = BoxGridRenderer()
    for i in range(15):
        widget.add_label(f"Label {i}")
    window.setCentralWidget(widget)
    window.show()
    app.exec()
