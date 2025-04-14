from typing import Callable

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QWidget

from model.macro import Macro, Trigger, trigger_factory


class _NewTriggerDialog(QDialog):
    def __init__(self, parent: QWidget, macro: Macro):
        super().__init__(parent)
        self._macro = macro
        self.setModal(True)
        self.setWindowTitle(f"Add Trigger to Macro {macro.name}")
        self._button_box = QDialogButtonBox(
            (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        )
        self._button_box.rejected.connect(self.close)
        self._button_box.accepted.connect(self._apply)
        layout = QFormLayout()
        self._type_cb = QComboBox(self)
        self._type_cb.addItems(Trigger.SUPPORTED_TYPES)
        self._type_cb.setEditable(False)
        layout.addRow("Type", self._type_cb)
        self._name_tb = QLineEdit(self)
        self._name_tb.setPlaceholderText("trigger name")
        layout.addRow("Name", self._name_tb)
        layout.addWidget(self._button_box)
        self.setLayout(layout)
        self.added_callable: Callable | None = None

    def _apply(self):
        type_str = self._type_cb.currentText()
        t = trigger_factory(type_str)
        t.name = self._name_tb.text() or "New Trigger"
        self._macro.add_trigger(t)
        self.close()
        if self.added_callable is not None:
            self.added_callable(t)
