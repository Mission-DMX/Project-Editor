from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QWidget

from model.macro import Macro


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
        # TODO add required widgets
        layout.addWidget(self._button_box)
        self.setLayout(layout)

    def _apply(self):
        # TODO construct trigger and add it to self._macro
        self.close()