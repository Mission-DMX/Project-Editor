from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout

from Style import Style
from view.utility_widgets.color_picker.color_picker_widget import ColorPickerWidget

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    window = QtWidgets.QMainWindow()
    layout = QVBoxLayout()
    widget = ColorPickerWidget(window)
    layout.addWidget(widget)
    window.setLayout(layout)
    window.showMaximized()
    app.exec()
