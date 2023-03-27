from PySide6 import QtWidgets


class CustomEditorDialog(QtWidgets.QDialog):
    """Dialog to choose a channel from a universe.

    Asks for a universe and channel and optional description.
    The description is set to 'Universe x Channel y' by default.
    Universe and channel input is considered to be 1-indexed.
    """
    def __init__(self, parent=None):
        """Inits the CustomEditorDialog.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent=parent)

        self.setWindowTitle("Choose a channel")

        layout = QtWidgets.QFormLayout(self)
        self._universe_label = QtWidgets.QLabel("Universe")
        self._universe_input = QtWidgets.QLineEdit()
        layout.addRow(self._universe_label, self._universe_input)

        self._channel_label = QtWidgets.QLabel("Channel")
        self._channel_input = QtWidgets.QLineEdit()
        layout.addRow(self._channel_label, self._channel_input)

        self._description_label = QtWidgets.QLabel("Description")
        self._description_input = QtWidgets.QLineEdit()
        layout.addRow(self._description_label, self._description_input)

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        layout.addWidget(btn_box)

        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    def get_inputs(self) -> tuple[int, int, str]:
        """The user inputs in the dialog.

        Returns:
            A 3-tuple containing:

            universe address (0-indexed)
            channel address (0-indexed)
            description
        """
        return int(self._universe_input.text()) - 1, int(self._channel_input.text()) - 1, self._description_input.text()