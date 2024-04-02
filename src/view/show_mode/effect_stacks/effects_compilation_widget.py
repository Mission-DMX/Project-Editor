from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget


class EffectCompilationWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.setMinimumWidth(600)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: gray;")
