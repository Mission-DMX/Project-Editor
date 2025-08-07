from collections.abc import Callable

from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QLineEdit, QPushButton, QWidget

from model import DataType


class ChannelInputDialog(QDialog):
    """Dialog to add a new channel to a preview edit widgets model."""

    def __init__(self, parent: QWidget, ok_function: Callable[[str, DataType], None]) -> None:
        """Channel input dialog.

        Args:
            parent: Parent QWidget.
            ok_function: Function called when the user presses the OK button. It receives
                the name of the new channel and the selected data type.

        """

        super().__init__(parent)
        self._ok_function = ok_function
        self._layout = QFormLayout()
        self._channel_name = QLineEdit()
        self._layout.addRow("Channel name:", self._channel_name)
        self._type_box = QComboBox()
        self._type_box.addItems(DataType.names())
        self._type_box.setCurrentIndex(3)  # Should be color
        self._layout.addRow("Channel Type:", self._type_box)
        self._ok_button = QPushButton("Add Channel")
        self._ok_button.pressed.connect(self._ok_pressed)
        self._layout.addRow("", self._ok_button)
        self.setLayout(self._layout)

    def _ok_pressed(self) -> None:
        self._ok_function(self._channel_name.text(), DataType.from_filter_str(self._type_box.currentText()))
        self.close()
