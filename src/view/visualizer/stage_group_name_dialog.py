"""Contains stage editor's GroupNameDialog."""

from __future__ import annotations

from PySide6 import QtWidgets

from model.visualizer.stage.stage_config import make_unique_name


class GroupNameDialog(QtWidgets.QDialog):
    """Simple dialog that asks the user for a group name."""

    def __init__(self, existing_names: list[str], parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the dialog."""
        super().__init__(parent)
        self.setWindowTitle("Create Group")
        self.setModal(True)
        self.setMinimumWidth(250)
        self.setMaximumWidth(400)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self._name_edit = QtWidgets.QLineEdit()
        suggested = make_unique_name("Group", existing_names)
        self._name_edit.setPlaceholderText(suggested)
        form.addRow("Group name:", self._name_edit)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def selected_name(self) -> str:
        """Get the selected name of the group."""
        text = self._name_edit.text().strip()
        return text or self._name_edit.placeholderText()
