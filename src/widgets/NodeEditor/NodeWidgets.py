from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QInputDialog, QGraphicsSceneMouseEvent, QGraphicsTextItem
from PySide6.QtCore import Qt

from DMXModel import Filter


class InitialParameterTextItem(QGraphicsTextItem):
    def __init__(self, text, parent, on_update, filter: Filter):
        super().__init__(text, parent)
        self.on_update = on_update
        self.filter = filter

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        if self.on_update is not None:
            self.on_update()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Enter or ev.key() == Qt.Key.Key_Return:
            if self.on_update is not None:
                self.on_update()
                return
        super().keyPressEvent(ev)
        
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.setFocus(Qt.FocusReason.MouseFocusReason)  # focus text label
        elif ev.button() == Qt.MouseButton.RightButton:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        


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
