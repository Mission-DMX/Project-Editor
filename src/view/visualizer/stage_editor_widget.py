import logging
from PySide6 import QtWidgets, QtCore

from model.stage import Truss

logger = logging.getLogger(__file__)


class StageEditorWidget(QtWidgets.QWidget):
    addObjectRequested = QtCore.Signal(type)  # Signal for wanting to add a new object
    removeObjectRequested = QtCore.Signal(str)  # Signal for removing an object
    objectChanged = QtCore.Signal(str)  # Signal when an object is changed (position, etc.)

    def __init__(self, stage_config, parent=None):
        super().__init__(parent)
        self._stage_config = stage_config
        main_layout = QtWidgets.QVBoxLayout(self)
        btn_layout = QtWidgets.QHBoxLayout()
        self._add_btn = QtWidgets.QPushButton("+")
        self._remove_btn = QtWidgets.QPushButton("-")
        btn_layout.addWidget(QtWidgets.QLabel("Objects:"))
        btn_layout.addStretch(1)
        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        main_layout.addLayout(btn_layout)

        self._object_list = QtWidgets.QListWidget()
        main_layout.addWidget(self._object_list)

        self._prop_group = QtWidgets.QGroupBox("Selected Object Properties")
        prop_layout = QtWidgets.QFormLayout()

        self._pos_x_spin = QtWidgets.QDoubleSpinBox()
        self._pos_x_spin.setRange(-1000.0, 1000.0)
        self._pos_x_spin.setDecimals(1)
        self._pos_x_spin.setSingleStep(0.1)
        self._pos_y_spin = QtWidgets.QDoubleSpinBox()
        self._pos_y_spin.setRange(-1000.0, 1000.0)
        self._pos_y_spin.setDecimals(1)
        self._pos_y_spin.setSingleStep(0.1)
        self._pos_z_spin = QtWidgets.QDoubleSpinBox()
        self._pos_z_spin.setRange(-1000.0, 1000.0)
        self._pos_z_spin.setDecimals(1)
        self._pos_z_spin.setSingleStep(0.1)
        prop_layout.addRow("Position X:", self._pos_x_spin)
        prop_layout.addRow("Position Y:", self._pos_y_spin)
        prop_layout.addRow("Position Z:", self._pos_z_spin)

        self._rot_x_spin = QtWidgets.QDoubleSpinBox()
        self._rot_x_spin.setRange(-360.0, 360.0)
        self._rot_x_spin.setDecimals(1)
        self._rot_x_spin.setSingleStep(1.0)
        self._rot_y_spin = QtWidgets.QDoubleSpinBox()
        self._rot_y_spin.setRange(-360.0, 360.0)
        self._rot_y_spin.setDecimals(1)
        self._rot_y_spin.setSingleStep(1.0)
        self._rot_z_spin = QtWidgets.QDoubleSpinBox()
        self._rot_z_spin.setRange(-360.0, 360.0)
        self._rot_z_spin.setDecimals(1)
        self._rot_z_spin.setSingleStep(1.0)
        prop_layout.addRow("Rotation X:", self._rot_x_spin)
        prop_layout.addRow("Rotation Y:", self._rot_y_spin)
        prop_layout.addRow("Rotation Z:", self._rot_z_spin)
        self._prop_group.setLayout(prop_layout)
        main_layout.addWidget(self._prop_group)

        self._prop_group.setEnabled(False)

        self._add_btn.clicked.connect(self._on_add_clicked)
        self._remove_btn.clicked.connect(self._on_remove_clicked)
        self._object_list.currentItemChanged.connect(self._on_selection_changed)

        self._pos_x_spin.valueChanged.connect(self._on_position_spin)
        self._pos_y_spin.valueChanged.connect(self._on_position_spin)
        self._pos_z_spin.valueChanged.connect(self._on_position_spin)
        self._rot_x_spin.valueChanged.connect(self._on_rotation_spin)
        self._rot_y_spin.valueChanged.connect(self._on_rotation_spin)
        self._rot_z_spin.valueChanged.connect(self._on_rotation_spin)

        for obj in self._stage_config.objects:
            self._add_list_item(obj)

    def _add_list_item(self, obj):
        item_text = f"{obj.id} [{obj.get_type()}]"
        item = QtWidgets.QListWidgetItem(item_text)
        item.setData(QtCore.Qt.UserRole, obj.id)
        self._object_list.addItem(item)

    def _on_add_clicked(self):
        object_type = Truss #TODO: Add support for multiple types
        logger.info("Add object requested (type: %s)", object_type)
        self.addObjectRequested.emit(object_type)

    def _on_remove_clicked(self):
        item = self._object_list.currentItem()
        if not item:
            return
        obj_id = item.data(QtCore.Qt.UserRole)
        logger.info("Remove object requested (id: %s)", obj_id)
        self.removeObjectRequested.emit(obj_id)

    def _on_selection_changed(self, current, previous):
        if current is None:
            self._prop_group.setEnabled(False)
            return
        self._prop_group.setEnabled(True)
        obj_id = current.data(QtCore.Qt.UserRole)
        obj = self._stage_config.get_object(obj_id)
        if obj:
            self._pos_x_spin.blockSignals(True)
            self._pos_y_spin.blockSignals(True)
            self._pos_z_spin.blockSignals(True)
            self._rot_x_spin.blockSignals(True)
            self._rot_y_spin.blockSignals(True)
            self._rot_z_spin.blockSignals(True)
            self._pos_x_spin.setValue(obj.position[0])
            self._pos_y_spin.setValue(obj.position[1])
            self._pos_z_spin.setValue(obj.position[2])
            self._rot_x_spin.setValue(obj.rotation[0])
            self._rot_y_spin.setValue(obj.rotation[1])
            self._rot_z_spin.setValue(obj.rotation[2])
            self._pos_x_spin.blockSignals(False)
            self._pos_y_spin.blockSignals(False)
            self._pos_z_spin.blockSignals(False)
            self._rot_x_spin.blockSignals(False)
            self._rot_y_spin.blockSignals(False)
            self._rot_z_spin.blockSignals(False)

    def _on_position_spin(self):
        item = self._object_list.currentItem()
        if not item:
            return
        obj_id = item.data(QtCore.Qt.UserRole)
        obj = self._stage_config.get_object(obj_id)
        if obj:
            obj.position = (self._pos_x_spin.value(), self._pos_y_spin.value(), self._pos_z_spin.value())
            self.objectChanged.emit(obj_id)

    def _on_rotation_spin(self):
        item = self._object_list.currentItem()
        if not item:
            return
        obj_id = item.data(QtCore.Qt.UserRole)
        obj = self._stage_config.get_object(obj_id)
        if obj:
            obj.rotation = (self._rot_x_spin.value(), self._rot_y_spin.value(), self._rot_z_spin.value())
            self.objectChanged.emit(obj_id)

    def add_object_to_list(self, obj):
        self._add_list_item(obj)
        # Select the new object automatically
        self._object_list.setCurrentRow(self._object_list.count() - 1)

    def remove_object_from_list(self, object_id):
        for i in range(self._object_list.count()):
            item = self._object_list.item(i)
            if item.data(QtCore.Qt.UserRole) == object_id:
                self._object_list.takeItem(i)
                break
