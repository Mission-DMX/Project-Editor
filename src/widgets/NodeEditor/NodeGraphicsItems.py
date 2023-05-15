from enum import Enum
import logging

from PySide6.QtWidgets import QLineEdit, QLabel, QPushButton, QGraphicsItem, QGraphicsPixmapItem, QDialog, QFormLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


from model.board_configuration import Filter, UniverseFilter
from model.patching_channel import PatchingChannel
from model.universe import Universe

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
            FilterSettingsDialog(self.filter).exec()


class FilterSettingsDialog(QDialog):
    def __init__(self, filter: Filter) -> None:
        super().__init__()
        self.filter = filter
        self.setWindowTitle("Filter Settings")
        
        layout = QFormLayout()
        
        add_patch_info = None if not isinstance(filter, UniverseFilter) else self._add_patch_info
        
        if len(filter.initial_parameters) > 0:
            layout.addRow("Initial Parameters", QLabel(""))
            
            for key, value in filter.initial_parameters.items():
                le = QLineEdit()
                le.setText(value)
                le.textChanged.connect(lambda new_value: self._ip_value_changed(key, new_value))
                layout.addRow(key, le)
        
        if len(filter.filter_configurations) > 0:
            layout.addRow("Filter Configurations", QLabel(""))
            
            for key, value in filter.filter_configurations.items():
                le = QLineEdit()
                le.setText(value)
                le.textChanged.connect(lambda new_value: self._fc_value_changed(key, new_value))
                key = add_patch_info(key, value)
                layout.addRow(key, le)

        self._ok_button = QPushButton("Ok")
        self._ok_button.pressed.connect(self.close)

        layout.addRow("", self._ok_button)

        self.setLayout(layout)
    
    def _add_patch_info(self, key: str, value: str) -> str:
        if not isinstance(self.filter, UniverseFilter):
            return key
        
        if key == "universe":
            return key
        
        id = int(self.filter.filter_configurations["universe"])
        universe: Universe = None
        for uni in self.filter.board_configuration.universes:
            if uni.universe_proto.id == id:
                universe = uni
                break
        else:
            logging.warn(f"Could not find universe {id}.")
            return key
        
        patching: PatchingChannel = None
        for channel in universe.patching:
            if channel.address == int(value):
                key = f"{key} : {channel.fixture.short_name}"
                
        return key

    def _ip_value_changed(self, key, value):
        self.filter.initial_parameters[key] = value
        
    def _fc_value_changed(self, key, value):
        self.filter.filter_configurations[key] = value