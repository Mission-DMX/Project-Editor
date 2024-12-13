from PySide6.QtWidgets import QWidget, QHBoxLayout, QButtonGroup


class ButtonContainer(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.button_gl = QHBoxLayout()
        self.setLayout(self.button_gl)
        self.button_group = QButtonGroup(parent)

    def add_button(self, button: QWidget):
        self.button_group.addButton(button)
        self.button_gl.addWidget(button)
