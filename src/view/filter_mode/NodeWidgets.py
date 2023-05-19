from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class Constants8BitWidget(QWidget):
    """QWidget to be displayed for a Constants8BitNode"""
    def __init__(self) -> None:
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("8Bit"))


class ConstantsColorWidget(QWidget):
    """QWidget to be displayed for a ConstantsColorNode"""
    def __init__(self) -> None:
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Color"))


class ColorToRGBWidget(QWidget):
    """QWidget to be displayed for a ColorToRGBNode"""
    def __init__(self) -> None:
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Color->RGB"))


class UniverseWidget(QWidget):
    """QWidget to be displayed for a UniverseNode"""
    def __init__(self) -> None:
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Universe"))
