from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout

from Style import Style
from view.utility_widgets.color_picker import opengl_context_init
from view.utility_widgets.color_picker.color_picker_widget import ColorPickerWidget

if __name__ == "__main__":
    opengl_context_init()
    QtWidgets.QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    window = QtWidgets.QMainWindow()
    layout = QVBoxLayout()
    widget = ColorPickerWidget(window)
    layout.addWidget(widget)
    window.setLayout(layout)
    window.showMaximized()
    app.exec()
