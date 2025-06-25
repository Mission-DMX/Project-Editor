from PySide6 import QtWidgets
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from view.utility_widgets.box_grid_renderer import BoxGridRenderer

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setDesktopSettingsAware(True)
    window = QMainWindow()

    widget = BoxGridRenderer()
    for i in range(15):
        widget.add_label(f"Label {i}")
    widget.item_at(4).set_icon(QIcon.fromTheme("list-add"))
    widget.item_at(4).clicked.connect(lambda: print("click"))
    window.setCentralWidget(widget)
    window.show()
    app.exec()
