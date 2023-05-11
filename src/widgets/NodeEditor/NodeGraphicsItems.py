from enum import Enum

from PySide6.QtWidgets import QLineEdit, QLabel, QGraphicsItem, QGraphicsPixmapItem, QDialog, QFormLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


from DMXModel import Filter

class FilterSettingsItem(QGraphicsPixmapItem):
    
    
    class SettingsType(Enum):
        INITIAL_PARAMETERS = "IP", "Initial Parameters"
        FILTER_CONFIGURATION = "FC", "Filter Configuration"
    
    
    def __init__(self, filter: Filter, parent: QGraphicsItem):
        super().__init__(QPixmap("resources/settings.svg").scaled(10, 10), parent)
        self.filter = filter
        self.on_update = lambda: None
        self.moveBy(parent.boundingRect().width()/2, parent.boundingRect().height() - 20)

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
            #self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            #self.setFocus(Qt.FocusReason.MouseFocusReason)  # focus text label
            FilterSettingsDialog(self).exec()
        elif ev.button() == Qt.MouseButton.RightButton:
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)


class FilterSettingsDialog(QDialog):
    def __init__(self, item: FilterSettingsItem) -> None:
        super().__init__()
        self.item = item
        self.setWindowTitle("Filter Settings")
        layout = QFormLayout()
        
        layout.addRow("Initial Parameters", QLabel(""))
        
        for key, value in item.filter.initial_parameters.items():
            le = QLineEdit()
            le.setText(value)
            le.textChanged.connect(lambda new_value: self._ip_value_changed(key, new_value))
            layout.addRow(key, le)
            
        layout.addRow("Filter Configurations", QLabel(""))
            
        for key, value in item.filter.filter_configurations.items():
            le = QLineEdit()
            le.setText(value)
            le.textChanged.connect(lambda new_value: self._fc_value_changed(key, new_value))
            layout.addRow(key, le)
        
        self.setLayout(layout)

    def _ip_value_changed(self, key, value):
        self.item.filter.initial_parameters[key] = value
        
    def _fc_value_changed(self, key, value):
        self.item.filter.filter_configurations[key] = value