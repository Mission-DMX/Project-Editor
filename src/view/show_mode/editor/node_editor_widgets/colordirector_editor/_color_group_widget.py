"""Contains ColorGroupWidget."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QMessageBox, QPushButton, QTreeWidget, QVBoxLayout, QWidget

from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem

if TYPE_CHECKING:
    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter


class ColorGroupWidget(QWidget):
    """Widget to edit color groups in color director vfilter."""

    def __init__(self, model: ColordirectorVFilter, parent: QWidget | None = None) -> None:
        """Initialize using given model and optional parent."""
        super().__init__(parent)
        self._model: ColordirectorVFilter = model
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self._add_group_button = QPushButton("Add Group")
        self._add_group_button.clicked.connect(self._add_group)
        button_layout.addWidget(self._add_group_button)
        self._add_sub_output_button = QPushButton("Add Sub Output")
        self._add_sub_output_button.clicked.connect(self._add_sub_output)
        self._add_sub_output_button.setEnabled(False)
        button_layout.addWidget(self._add_sub_output_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        self._group_view = QTreeWidget(self)
        self._group_view.itemSelectionChanged.connect(self._selected_group_changed)
        self._group_view.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._group_view)
        self.setLayout(layout)
        self._input_dialog: QInputDialog | None = None
        self._refresh_tree_view()

    def _refresh_tree_view(self) -> None:
        for group, outputs in self._model.output_groups.items():
            group_item = AnnotatedTreeWidgetItem(self._group_view)
            group_item.setText(0, group)
            group_item.annotated_data = (True, group)
            for output in outputs:
                output_item = AnnotatedTreeWidgetItem(group_item)
                output_item.setText(0, output)
                output_item.annotated_data = (False, output)
            group_item.setExpanded(True)
            self._group_view.addTopLevelItem(group_item)

    def _selected_group_changed(self) -> None:
        item = self._group_view.selectedItems()[0]
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        self._add_sub_output_button.setEnabled(item.annotated_data[0])

    def _add_group(self) -> None:
        self._input_dialog = QInputDialog(self)
        self._input_dialog.setModal(True)
        self._input_dialog.setLabelText("Please input group name:")
        self._input_dialog.setInputMode(QInputDialog.InputMode.TextInput)
        self._input_dialog.accepted.connect(self._add_group_final)
        self._input_dialog.show()

    def _add_group_final(self) -> None:
        name = self._input_dialog.textValue()
        self._input_dialog.deleteLater()
        if name in self._model.output_groups:
            self._input_dialog = QMessageBox()
            self._input_dialog.setWindowTitle("Group Already Exists")
            self._input_dialog.setText("Group names need to be unique.")
            self._input_dialog.setIcon(QMessageBox.Icon.Critical)
            self._input_dialog.show()
            return
        self._model.output_groups[name] = []
        group_item = AnnotatedTreeWidgetItem(self._group_view)
        group_item.setText(0, name)
        group_item.annotated_data = (True, name)
        self._group_view.addTopLevelItem(group_item)

    def _add_sub_output(self) -> None:
        pass  # TODO add sub output of selected group to model and view
