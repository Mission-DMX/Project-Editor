from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from model import events
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class EventSelectionDialog(QDialog):
    """This dialog prompts the user to select an event to link."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the event selection dialog."""
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Select Event")
        self.selected_event: tuple[int, int, str] = (0, 0, "")
        layout = QFormLayout()
        self._event_tree = QTreeWidget(self)
        self._event_tree.itemSelectionChanged.connect(self._event_selected_from_tree)
        layout.addRow(self._event_tree)
        self._fill_event_tree()
        self._sender_tb = QSpinBox(self)
        self._sender_tb.valueChanged.connect(self._sender_value_changed)
        self._sender_tb.setMinimum(0)
        layout.addRow("Sender", self._sender_tb)
        self._function_tb = QSpinBox(self)
        self._function_tb.valueChanged.connect(self._function_value_changed)
        self._function_tb.setMinimum(0)
        layout.addRow("Function", self._function_tb)
        self._argument_tb = QLineEdit(self)
        self._argument_tb.setInputMask("9999999")
        self._argument_tb.textChanged.connect(self._arguments_changed)
        layout.addRow("Arguments", self._argument_tb)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                      Qt.Orientation.Horizontal, self)
        layout.addRow(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.setLayout(layout)

    def accept(self) -> None:
        """Callback of the dialog accept signal. Automatically closes the dialog."""
        super().accept()
        self.close()

    def reject(self) -> None:
        """Callback of the dialog reject signal. Automatically closes the dialog."""
        super().reject()
        self.close()

    def _fill_event_tree(self) -> None:
        """Load the event tree with events found in the show file."""
        for event_sender in events.get_all_senders():
            sender_item = QTreeWidgetItem(self._event_tree)
            sender_item.setFlags(sender_item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEditable)
            sender_item.setText(0, event_sender.name)
            for event, event_name in event_sender.renamed_events.items():
                event_item = AnnotatedTreeWidgetItem(sender_item)
                event_item.setText(0, event_name)
                event_item.setFlags(event_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                event_item.annotated_data = event
                sender_item.addChild(event_item)
            sender_item.setExpanded(True)
            self._event_tree.addTopLevelItem(sender_item)

    def _event_selected_from_tree(self) -> None:
        """Callback to handle a user selection of a specific event."""
        if len(self._event_tree.selectedItems()) < 1:
            return
        selected_item = self._event_tree.selectedItems()[0]
        if not isinstance(selected_item, AnnotatedTreeWidgetItem):
            return
        event = selected_item.annotated_data
        if not isinstance(event, tuple):
            return
        self._sender_tb.setValue(event[0])
        self._function_tb.setValue(event[1])
        self._argument_tb.setText(event[2])

    def _sender_value_changed(self) -> None:
        """Callback to update the selected event if the user manually updated the event sender."""
        self.selected_event = (self._sender_tb.value(), self.selected_event[1], self.selected_event[2])

    def _function_value_changed(self) -> None:
        """Callback to update the selected event if the user manually updated the event function."""
        self.selected_event = (self.selected_event[0], self._function_tb.value(), self.selected_event[2])

    def _arguments_changed(self) -> None:
        """Callback to update the selected event if the user manually updated the event arguments."""
        self.selected_event = (self.selected_event[0], self.selected_event[1], self._argument_tb.text())
