
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QWidget

from model.macro import Macro, Trigger, trigger_factory

if TYPE_CHECKING:
    from collections.abc import Callable


class _NewTriggerDialog(QDialog):
    """
    Dialog to add new macro triggers.
    Upon Accept this dialog adds the new trigger to the provided macro on its own.
    """

    def __init__(self, parent: QWidget, macro: Macro) -> None:
        super().__init__(parent)
        self._macro = macro
        self.setModal(True)
        self.setWindowTitle(f"Add Trigger to Macro {macro.name}")
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._button_box.rejected.connect(self.close)
        self._button_box.accepted.connect(self._apply)
        layout = QFormLayout()
        self._type_cb = QComboBox(self)
        self._type_cb.addItems(Trigger.SUPPORTED_TYPES)
        self._type_cb.currentTextChanged.connect(self._type_changed)
        self._type_cb.setEditable(False)
        layout.addRow("Type", self._type_cb)
        self._name_tb = QLineEdit(self)
        self._name_tb.setPlaceholderText("trigger name")
        layout.addRow("Name", self._name_tb)

        self._fbutton_cb = QComboBox(self)
        self._fbutton_cb.setEditable(False)
        self._fbutton_cb.addItems([f"F{str(i + 1)}" for i in range(8)])
        self._fbutton_cb.setEnabled(False)
        layout.addRow("Internal Macro Button", self._fbutton_cb)

        layout.addWidget(self._button_box)
        self.setLayout(layout)
        self.added_callable: Callable | None = None

    def _apply(self) -> None:
        type_str = self._type_cb.currentText()
        t = trigger_factory(type_str)
        t.name = self._name_tb.text() or "New Trigger"
        if self._type_cb.currentText() == "f_keys":
            t.set_param("button", str(int(self._fbutton_cb.currentText().replace("F", "")) - 1))
        self._macro.add_trigger(t)
        self.close()
        if self.added_callable is not None:
            self.added_callable(t)

    def _type_changed(self) -> None:
        self._fbutton_cb.setEnabled(self._type_cb.currentText() == "f_keys")
