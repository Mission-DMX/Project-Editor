"""Dialog to query data on channel add."""
from collections.abc import Callable
from logging import getLogger

from PySide6 import QtGui, QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDialog, QFormLayout, QLineEdit, QPushButton, QWidget, QStyle, \
    QDialogButtonBox, QSpinBox, QVBoxLayout, QTableWidget, QTableWidgetItem

from model import DataType

logger = getLogger(__name__)


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
        self._ok_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton))
        self._ok_button.pressed.connect(self._ok_pressed)
        self._layout.addRow("", self._ok_button)
        self.setLayout(self._layout)

    def _ok_pressed(self) -> None:
        self._ok_function(self._channel_name.text(), DataType.from_filter_str(self._type_box.currentText()))
        self.close()


class MultiChannelInputDialog(QDialog):
    """Dialog to add multiple channels to a preview edit widgets model."""

    def __init__(self, parent: QWidget, ok_function: Callable[[str, DataType], None]) -> None:
        """Multi Channel input dialog.

        Args:
            parent: Parent QWidget.
            ok_function: Function called when the user presses the OK button. It receives
                the name of the new channel and the selected data type.

        """
        super().__init__(parent)
        self._ok_function = ok_function
        self._layout = QVBoxLayout()
        self._form_layout = QFormLayout()

        self._iteration_number_box = QSpinBox(self)
        self._iteration_number_box.setRange(1, 16384)
        self._iteration_number_box.setValue(1)
        self._form_layout.addRow("Number of Invocations:", self._iteration_number_box)

        self._name_template_tb = QLineEdit(self)
        self._name_template_tb.setText("{i}_{name}")
        self._name_template_tb.setToolTip("Please specify the name template. You may use {i} to specify the iteration, "
                                          "{name} the channel name from the table below abd {dt} for its data type.")
        self._form_layout.addRow("Name Template:", self._name_template_tb)
        self._layout.addLayout(self._form_layout)

        self._channel_tabel = QTableWidget(self)
        self._channel_tabel.setColumnCount(2)
        self._channel_tabel.setRowCount(0)
        self._channel_tabel.setHorizontalHeaderLabels(["Type", "Name"])
        self._add_row()
        self._layout.addWidget(self._channel_tabel)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        self._button_box.accepted.connect(self._perform_insertion)
        self._button_box.rejected.connect(self.close)
        self._layout.addWidget(self._button_box)
        self.setLayout(self._layout)

    def _add_row(self) -> None:
        self._channel_tabel.setRowCount(self._channel_tabel.rowCount() + 1)
        combo_box = QComboBox(self._channel_tabel)
        combo_box.addItems(DataType.names())
        combo_box.addItem("None")
        combo_box.setCurrentIndex(5)
        new_rows_index = self._channel_tabel.rowCount() - 1
        combo_box.currentIndexChanged.connect(lambda new_index, i=new_rows_index: self._check_row_add(i, new_index))
        self._channel_tabel.setCellWidget(new_rows_index, 0, combo_box)
        QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)
        name_item = QTableWidgetItem("")
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._channel_tabel.setItem(new_rows_index, 1, name_item)

    def _check_row_add(self, row: int, cb_index: int) -> None:
        name_item = self._channel_tabel.item(row, 1)
        if cb_index != 5:
            name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
            if row == self._channel_tabel.rowCount() - 1:
                self._add_row()
        else:
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def _perform_insertion(self):
        for i in range(self._iteration_number_box.value()):
            for channel_row in range(self._channel_tabel.rowCount()):
                data_type_cb = self._channel_tabel.cellWidget(channel_row, 0)
                if not isinstance(data_type_cb, QComboBox):
                    logger.error(f"Channel row {channel_row} is not a combo box.")
                    continue
                select_data_type = data_type_cb.currentText()
                if select_data_type != "None" and select_data_type != "":
                    row__text = self._channel_tabel.item(channel_row, 1).text()
                    if len(row__text) == 0:
                        logger.warning(f"Channel in row {channel_row} was skipped due to empty name.")
                        continue
                    text = self._name_template_tb.text().format(
                        i=i,
                        dt=select_data_type,
                        name=row__text
                    )
                    select_data_type = DataType.from_filter_str(select_data_type)
                    self._ok_function(text, select_data_type)
        self.close()
